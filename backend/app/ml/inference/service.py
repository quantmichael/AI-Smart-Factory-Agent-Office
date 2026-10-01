"""Load the baseline artifact and return the shared AnalysisResult contract."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import joblib
import numpy as np

from app.data.adapters.base import SensorDatasetAdapter
from app.domain.schemas import AnalysisResult
from app.ml.dataset import build_feature_table


class ModelNotFoundError(FileNotFoundError):
    pass


class InvalidFeatureError(ValueError):
    pass


class InferenceError(RuntimeError):
    pass


class ModelLoadError(InferenceError):
    pass


STATUS_BY_CLASS = {"healthy": "normal", "damaged": "abnormal"}
KEY_SIGNAL_FEATURES = (
    "vibration_1__rms",
    "vibration_1__kurtosis",
    "vibration_1__crest_factor",
    "vibration_1__dominant_frequency_hz",
)


class _SingleMeasurementAdapter(SensorDatasetAdapter):
    def __init__(self, delegate: SensorDatasetAdapter, measurement_id: str):
        self.delegate = delegate
        self.summary = delegate.get_metadata(measurement_id)
        self.load_seconds = 0.0

    def list_measurements(self):
        return (self.summary,)

    def load_measurement(self, measurement_id: str):
        started = perf_counter()
        measurement = self.delegate.load_measurement(measurement_id)
        self.load_seconds += perf_counter() - started
        return measurement

    def get_metadata(self, measurement_id: str):
        return self.delegate.get_metadata(measurement_id)

    def validate(self):
        return self.delegate.validate()


class MLInferenceService:
    def __init__(
        self,
        adapter: SensorDatasetAdapter,
        model_path: Path | str,
        input_spec: dict,
    ):
        path = Path(model_path)
        if not path.is_file():
            raise ModelNotFoundError(f"model artifact not found: {path}")
        try:
            bundle = joblib.load(path)
        except Exception as exc:  # pragma: no cover - library-specific failures
            raise ModelLoadError(f"could not load model artifact: {path}") from exc
        required = {"model", "model_id", "feature_names", "classes"}
        if not isinstance(bundle, dict) or not required.issubset(bundle):
            raise InvalidFeatureError("model artifact does not contain the required contract")
        self.adapter = adapter
        self.bundle = bundle
        self.input_spec = input_spec
        self.artifact_metadata: dict = {}

    @classmethod
    def from_artifact(
        cls,
        adapter: SensorDatasetAdapter,
        artifact_directory: Path | str,
    ) -> "MLInferenceService":
        directory = Path(artifact_directory)
        spec_path = directory / "input_spec.json"
        if not spec_path.is_file():
            raise InvalidFeatureError(f"input specification not found: {spec_path}")
        metadata_path = directory / "metadata.json"
        if not metadata_path.is_file():
            raise InvalidFeatureError(f"model metadata not found: {metadata_path}")
        input_spec = json.loads(spec_path.read_text(encoding="utf-8"))
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        service = cls(adapter, directory / "model.joblib", input_spec)
        if metadata.get("model_id") != service.bundle["model_id"]:
            raise InvalidFeatureError("metadata and model artifact IDs do not match")
        if metadata.get("feature_list") != service.bundle["feature_names"]:
            raise InvalidFeatureError("metadata and model feature lists do not match")
        if metadata.get("feature_version") != service.bundle.get("feature_version"):
            raise InvalidFeatureError("metadata and model feature versions do not match")
        service.artifact_metadata = metadata
        return service

    def analyze(self, measurement_id: str, analysis_id: str | None = None) -> AnalysisResult:
        started = perf_counter()
        timed_adapter = _SingleMeasurementAdapter(self.adapter, measurement_id)
        feature_started = perf_counter()
        table = build_feature_table(
            timed_adapter,
            self.input_spec,
        )
        feature_seconds = perf_counter() - feature_started
        expected = tuple(self.bundle["feature_names"])
        if table.feature_names != expected:
            raise InvalidFeatureError("runtime feature order differs from the trained model")
        try:
            model_started = perf_counter()
            probabilities = self.bundle["model"].predict_proba(table.matrix())
            model_seconds = perf_counter() - model_started
        except Exception as exc:
            raise InferenceError(f"prediction failed for {measurement_id}") from exc
        classes = list(self.bundle["classes"])
        if "damaged" not in classes:
            raise InvalidFeatureError("trained model has no damaged class")
        damaged = probabilities[:, classes.index("damaged")]
        mean_damaged = float(np.mean(damaged))
        predicted_class = "damaged" if mean_damaged >= 0.5 else "healthy"
        confidence = mean_damaged if predicted_class == "damaged" else 1.0 - mean_damaged
        summary = self.adapter.get_metadata(measurement_id)
        signal_features = {
            name.removeprefix("vibration_1__"): float(
                np.mean([record.features[name] for record in table.records])
            )
            for name in KEY_SIGNAL_FEATURES
        }
        return AnalysisResult(
            analysis_id=analysis_id or f"analysis_{uuid4().hex}",
            measurement_id=measurement_id,
            model_id=self.bundle["model_id"],
            status=STATUS_BY_CLASS[predicted_class],
            predicted_class=predicted_class,
            confidence=confidence,
            anomaly_score=None,
            signal_features=signal_features,
            metadata={
                "bearing_id": summary.bearing_id,
                "operating_condition": summary.operating_condition.code,
                "window_aggregation": "mean damaged-class probability; threshold=0.5",
                "window_count": len(table.records),
                "mean_damaged_class_probability": mean_damaged,
                "model_version": self.bundle.get("model_version", "unknown"),
                "feature_version": self.bundle.get("feature_version", "unknown"),
                "inference_timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                "timing_ms": {
                    "measurement_load": timed_adapter.load_seconds * 1000.0,
                    "feature_extraction": max(
                        0.0, feature_seconds - timed_adapter.load_seconds
                    ) * 1000.0,
                    "model_inference": model_seconds * 1000.0,
                    "total": (perf_counter() - started) * 1000.0,
                },
                "inference_latency_ms": (perf_counter() - started) * 1000.0,
                "probability_note": "Model output; not a calibrated equipment failure probability.",
            },
        )
