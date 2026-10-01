"""Read-only, public-safe views over the active ML artifact bundle."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import Field

from app.domain.schemas.common import StrictSchema
from app.ml.inference import ModelNotFoundError
from app.ml.registry import ArtifactModelRegistry


class ModelArtifactMissingError(FileNotFoundError):
    """The configured active model or its required metadata is unavailable."""


class ModelArtifactInvalidError(ValueError):
    """An artifact exists but cannot be rendered safely."""


class ModelIdentity(StrictSchema):
    model_id: str
    model_type: str
    version: str
    task: str
    classes: list[str]
    trained_at: datetime
    dataset: str
    feature_version: str
    feature_count: int = Field(ge=0)


class ModelFeature(StrictSchema):
    name: str
    channel: str
    statistic: str


class FeatureImportance(StrictSchema):
    rank: int = Field(ge=1)
    feature: str
    importance: float = Field(ge=0)


class ModelMetricLevel(StrictSchema):
    sample_count: int = Field(ge=0)
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    roc_auc: float | None = None
    damaged_recall: float | None = None
    confusion_matrix: list[list[int]] = Field(default_factory=list)


class ModelEvaluation(StrictSchema):
    aggregation_rule: str | None = None
    levels: dict[str, ModelMetricLevel] = Field(default_factory=dict)


class ModelTrainingData(StrictSchema):
    dataset: str
    is_local_subset: bool
    split_method: str | None = None
    group_key: str | None = None
    test_ratio: float | None = None
    random_seed: int | None = None
    train_measurement_count: int | None = Field(default=None, ge=0)
    test_measurement_count: int | None = Field(default=None, ge=0)
    train_window_count: int | None = Field(default=None, ge=0)
    test_window_count: int | None = Field(default=None, ge=0)
    train_bearing_ids: list[str] = Field(default_factory=list)
    test_bearing_ids: list[str] = Field(default_factory=list)
    shared_bearing_ids: list[str] = Field(default_factory=list)
    measurement_overlap_count: int | None = Field(default=None, ge=0)
    leakage_check_passed: bool | None = None
    diagnostic_channels: list[str] = Field(default_factory=list)
    window_duration_sec: float | None = None
    overlap_percent: float | None = None
    sampling_rate_hz: float | None = None
    known_limitation: str | None = None


class CurrentModelView(StrictSchema):
    status: str
    model: ModelIdentity
    features: list[ModelFeature] = Field(default_factory=list)
    feature_importance: list[FeatureImportance] = Field(default_factory=list)
    evaluation: ModelEvaluation
    training_data: ModelTrainingData
    artifact_limitations: list[str] = Field(default_factory=list)


def _read_json(path: Path, *, required: bool = False) -> dict[str, Any]:
    if not path.is_file():
        if required:
            raise ModelArtifactMissingError(f"required artifact is missing: {path.name}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelArtifactInvalidError(f"invalid artifact: {path.name}") from exc
    if not isinstance(value, dict):
        raise ModelArtifactInvalidError(f"artifact must contain an object: {path.name}")
    return value


def _metric_level(value: Any) -> ModelMetricLevel | None:
    if not isinstance(value, dict):
        return None
    try:
        return ModelMetricLevel.model_validate(value)
    except Exception as exc:
        raise ModelArtifactInvalidError("metrics.json contains an invalid metric level") from exc


def _report_limitations(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ModelArtifactInvalidError("BASELINE_REPORT.md cannot be read") from exc
    limitations: list[str] = []
    in_section = False
    for line in lines:
        if line.strip() == "## Limitations":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.startswith("- "):
            limitations.append(line[2:].strip())
    return limitations


class ModelCatalogService:
    """Load display metadata without deserializing or exposing model.joblib."""

    def __init__(self, artifact_root: Path, active_model_id: str) -> None:
        self.artifact_root = Path(artifact_root)
        self.active_model_id = active_model_id

    def current(self) -> CurrentModelView:
        try:
            entry = ArtifactModelRegistry(
                self.artifact_root,
                self.active_model_id,
            ).get_active_model()
        except ModelArtifactInvalidError:
            raise
        except ModelNotFoundError as exc:
            raise ModelArtifactMissingError("active model artifact was not found") from exc
        except Exception as exc:
            if isinstance(exc, (json.JSONDecodeError, OSError, ValueError)):
                raise ModelArtifactInvalidError("active model metadata is invalid") from exc
            raise ModelArtifactMissingError("active model artifact was not found") from exc

        directory = entry.artifact_directory
        metadata = _read_json(directory / "metadata.json", required=True)
        features_payload = _read_json(directory / "feature_list.json")
        metrics = _read_json(directory / "metrics.json")
        split = _read_json(directory / "split.json")
        input_spec = _read_json(directory / "input_spec.json")

        raw_feature_names = features_payload.get("feature_names") or metadata.get("feature_list") or []
        if not isinstance(raw_feature_names, list) or not all(
            isinstance(item, str) for item in raw_feature_names
        ):
            raise ModelArtifactInvalidError("feature list is invalid")
        features = []
        for name in raw_feature_names:
            channel, separator, statistic = name.partition("__")
            if not separator:
                raise ModelArtifactInvalidError("feature name does not identify its channel")
            features.append(ModelFeature(name=name, channel=channel, statistic=statistic))

        class_mapping = metadata.get("class_mapping")
        if not isinstance(class_mapping, dict) or not class_mapping:
            raise ModelArtifactInvalidError("model class mapping is missing or invalid")
        classes = [str(name) for name in class_mapping]

        try:
            identity = ModelIdentity(
                model_id=str(metadata["model_id"]),
                model_type=str(metadata["model_type"]),
                version=str(metadata["version"]),
                task="binary_classification" if len(classes) == 2 else "classification",
                classes=classes,
                trained_at=metadata["trained_at"],
                dataset=str(metadata["dataset"]),
                feature_version=str(metadata["feature_version"]),
                feature_count=len(features),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ModelArtifactInvalidError("required model metadata is invalid") from exc

        importance = self._feature_importance(directory / "feature_importance.csv")
        levels: dict[str, ModelMetricLevel] = {}
        for key in ("window_level", "measurement_level", "bearing_level"):
            level = _metric_level(metrics.get(key))
            if level is not None:
                levels[key] = level

        train_bearings = sorted(str(item) for item in split.get("train_bearings", []))
        test_bearings = sorted(str(item) for item in split.get("test_bearings", []))
        overlap = split.get("leakage_validation", {})
        if overlap and not isinstance(overlap, dict):
            raise ModelArtifactInvalidError("split leakage validation is invalid")
        train_measurements = split.get("train_measurements")
        test_measurements = split.get("test_measurements")
        if train_measurements is not None and not isinstance(train_measurements, list):
            raise ModelArtifactInvalidError("train measurements are invalid")
        if test_measurements is not None and not isinstance(test_measurements, list):
            raise ModelArtifactInvalidError("test measurements are invalid")
        measurement_intersection = overlap.get("train_test_measurement_intersection", [])

        training_data = ModelTrainingData(
            dataset=identity.dataset,
            is_local_subset="subset" in identity.dataset.lower(),
            split_method=split.get("split_strategy") or metadata.get("split_strategy"),
            group_key=split.get("group_key") or metadata.get("group_key"),
            test_ratio=split.get("test_size"),
            random_seed=split.get("random_seed") or metadata.get("random_seed"),
            train_measurement_count=(len(train_measurements) if train_measurements is not None else None),
            test_measurement_count=(len(test_measurements) if test_measurements is not None else None),
            train_window_count=split.get("train_window_count"),
            test_window_count=split.get("test_window_count"),
            train_bearing_ids=train_bearings,
            test_bearing_ids=test_bearings,
            shared_bearing_ids=sorted(set(train_bearings) & set(test_bearings)),
            measurement_overlap_count=(
                len(measurement_intersection)
                if isinstance(measurement_intersection, list)
                else None
            ),
            leakage_check_passed=overlap.get("passed"),
            diagnostic_channels=[str(item) for item in input_spec.get("diagnostic_channels", [])],
            window_duration_sec=input_spec.get("window_duration_sec"),
            overlap_percent=input_spec.get("overlap_percent"),
            sampling_rate_hz=input_spec.get("sampling_rate_hz"),
            known_limitation=split.get("known_limitation"),
        )
        return CurrentModelView(
            status="READY",
            model=identity,
            features=features,
            feature_importance=importance,
            evaluation=ModelEvaluation(
                aggregation_rule=metrics.get("aggregation_rule"),
                levels=levels,
            ),
            training_data=training_data,
            artifact_limitations=_report_limitations(directory / "BASELINE_REPORT.md"),
        )

    @staticmethod
    def _feature_importance(path: Path) -> list[FeatureImportance]:
        if not path.is_file():
            return []
        try:
            with path.open(encoding="utf-8", newline="") as handle:
                return [
                    FeatureImportance(
                        rank=int(row["rank"]),
                        feature=row["feature"],
                        importance=float(row["importance"]),
                    )
                    for row in csv.DictReader(handle)
                ]
        except (OSError, KeyError, TypeError, ValueError) as exc:
            raise ModelArtifactInvalidError("feature_importance.csv is invalid") from exc
