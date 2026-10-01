"""Build leakage-auditable window feature tables from dataset adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from app.data.adapters.base import SensorDatasetAdapter
from app.ml.features.pipeline import extract_signal_features
from app.ml.windowing import window_bounds


@dataclass(frozen=True, slots=True)
class WindowFeatureRecord:
    measurement_id: str
    bearing_id: str
    operating_condition: str
    window_id: str
    window_start: int
    window_end: int
    ground_truth: str
    features: dict[str, float]


@dataclass(frozen=True, slots=True)
class MLFeatureTable:
    records: tuple[WindowFeatureRecord, ...]
    feature_names: tuple[str, ...]

    def matrix(self, records: Iterable[WindowFeatureRecord] | None = None) -> np.ndarray:
        selected = tuple(records) if records is not None else self.records
        return np.asarray(
            [[record.features[name] for name in self.feature_names] for record in selected],
            dtype=np.float64,
        )


def load_input_spec(path: Path | str) -> dict[str, Any]:
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {
        "diagnostic_channels",
        "window_duration_sec",
        "overlap_percent",
        "time_domain_features",
        "frequency_domain_features",
        "split",
    }
    missing = required.difference(spec)
    if missing:
        raise ValueError(f"STEP 04 input specification missing: {sorted(missing)}")
    if spec["split"].get("group") != "measurement_id":
        raise ValueError("STEP 03 split policy must use measurement_id")
    return spec


def build_feature_table(
    adapter: SensorDatasetAdapter,
    spec: dict[str, Any],
) -> MLFeatureTable:
    """Extract one feature row per fixed window without reading MAT internals."""

    channels = tuple(spec["diagnostic_channels"])
    selected_features = tuple(spec["time_domain_features"]) + tuple(
        spec["frequency_domain_features"]
    )
    feature_names = tuple(
        f"{channel}__{feature}" for channel in channels for feature in selected_features
    )
    duration = float(spec["window_duration_sec"])
    overlap = float(spec["overlap_percent"]) / 100.0
    records: list[WindowFeatureRecord] = []

    for summary in adapter.list_measurements():
        if summary.ground_truth.state not in {"healthy", "damaged"}:
            continue
        measurement = adapter.load_measurement(summary.measurement_id)
        missing_channels = set(channels).difference(measurement.signals)
        if missing_channels:
            raise ValueError(
                f"{summary.measurement_id} missing diagnostic channels: {sorted(missing_channels)}"
            )
        reference = measurement.signals[channels[0]]
        rate = reference.sampling.nominal_rate_hz
        if rate is None:
            raise ValueError(f"{summary.measurement_id} has no verified sampling rate")
        bounds = window_bounds(reference.values.size, rate, duration, overlap)
        for bound in bounds:
            row_features: dict[str, float] = {}
            for channel in channels:
                signal = measurement.signals[channel]
                channel_rate = signal.sampling.nominal_rate_hz
                if channel_rate != rate:
                    raise ValueError(
                        f"{summary.measurement_id} diagnostic sampling rates do not match"
                    )
                if signal.values.size < bound.end:
                    raise ValueError(
                        f"{summary.measurement_id}:{channel} is shorter than the reference channel"
                    )
                extracted = extract_signal_features(
                    signal.values[bound.start : bound.end],
                    rate,
                )
                for feature in selected_features:
                    value = float(extracted[feature])
                    if not np.isfinite(value):
                        raise ValueError(
                            f"non-finite feature for {summary.measurement_id}:{channel}:{feature}"
                        )
                    row_features[f"{channel}__{feature}"] = value
            records.append(
                WindowFeatureRecord(
                    measurement_id=summary.measurement_id,
                    bearing_id=summary.bearing_id,
                    operating_condition=summary.operating_condition.code,
                    window_id=bound.window_id,
                    window_start=bound.start,
                    window_end=bound.end,
                    ground_truth=summary.ground_truth.state,
                    features=row_features,
                )
            )
    if not records:
        raise ValueError("feature table is empty")
    return MLFeatureTable(records=tuple(records), feature_names=feature_names)
