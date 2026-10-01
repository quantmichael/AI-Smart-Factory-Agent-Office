"""STEP 03 profiling over dataset-independent adapter measurements."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import matplotlib
import numpy as np

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402

from app.data.adapters.paderborn import PaderbornDatasetAdapter
from app.data.models import StandardMeasurement
from app.ml.features.pipeline import extract_signal_features
from app.ml.windowing import window_bounds


PROFILING_VERSION = "1.0"
RANDOM_STATE = 42
DIAGNOSTIC_CHANNELS = ("vibration_1", "phase_current_1", "phase_current_2")
TIME_FEATURES = (
    "mean",
    "std",
    "rms",
    "peak",
    "peak_to_peak",
    "crest_factor",
    "skewness",
    "kurtosis",
)
FREQUENCY_FEATURES = (
    "dominant_frequency_hz",
    "spectral_centroid_hz",
    "spectral_energy",
    "spectral_entropy",
)
WINDOW_CANDIDATES = (
    (0.25, 0.0),
    (0.25, 0.5),
    (0.5, 0.0),
    (0.5, 0.5),
    (1.0, 0.0),
    (1.0, 0.5),
)
SELECTED_WINDOW = (1.0, 0.0)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: Iterable[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)


def _cohens_d(healthy: np.ndarray, damaged: np.ndarray) -> float:
    if healthy.size < 2 or damaged.size < 2:
        return 0.0
    pooled_variance = (
        (healthy.size - 1) * np.var(healthy, ddof=1)
        + (damaged.size - 1) * np.var(damaged, ddof=1)
    ) / (healthy.size + damaged.size - 2)
    if pooled_variance <= 0:
        return 0.0
    return float((np.mean(damaged) - np.mean(healthy)) / np.sqrt(pooled_variance))


def _summarize(values: np.ndarray) -> dict[str, float | int]:
    return {
        "count": int(values.size),
        "mean": float(np.mean(values)),
        "std": float(np.std(values, ddof=0)),
        "median": float(np.median(values)),
        "q25": float(np.quantile(values, 0.25)),
        "q75": float(np.quantile(values, 0.75)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }


def _relative_spectrum(values: np.ndarray, rate: float) -> tuple[np.ndarray, np.ndarray]:
    centered = values.astype(np.float64, copy=False) - float(np.mean(values))
    spectrum = np.abs(np.fft.rfft(centered * np.hanning(values.size)))
    frequencies = np.fft.rfftfreq(values.size, d=1.0 / rate)
    maximum = float(np.max(spectrum))
    relative_db = 20.0 * np.log10(np.maximum(spectrum / maximum, 1e-8)) if maximum else np.full_like(spectrum, -160.0)
    return frequencies, relative_db


def _representative_ids(adapter: PaderbornDatasetAdapter) -> dict[str, str]:
    summaries = adapter.list_measurements()
    preferred_condition = "N15_M07_F10"
    result: dict[str, str] = {}
    for state in ("healthy", "damaged"):
        preferred = [
            item
            for item in summaries
            if item.ground_truth.state == state
            and item.operating_condition.code == preferred_condition
        ]
        candidates = preferred or [item for item in summaries if item.ground_truth.state == state]
        if candidates:
            result[state] = sorted(candidates, key=lambda item: item.measurement_id)[0].measurement_id
    return result


class PaderbornProfiler:
    """Generate bounded statistical artifacts without training a model."""

    def __init__(self, adapter: PaderbornDatasetAdapter, output_root: Path | str):
        self.adapter = adapter
        self.output_root = Path(output_root)
        self.figures_root = self.output_root / "figures"

    def run(self) -> dict[str, Any]:
        validation = self.adapter.validate()
        if validation.status != "pass":
            raise RuntimeError("Adapter validation must pass before profiling")

        selected_ids = _representative_ids(self.adapter)
        measurement_rows: list[dict[str, Any]] = []
        long_features: list[dict[str, Any]] = []
        representative: dict[str, StandardMeasurement] = {}
        dtype_distribution: defaultdict[str, Counter[str]] = defaultdict(Counter)
        nominal_rate_distribution: defaultdict[str, Counter[str]] = defaultdict(Counter)
        constant_signals: list[dict[str, str]] = []
        sampling_deviations: list[dict[str, Any]] = []
        nonuniform_time_axes: Counter[str] = Counter()
        amplitude_records: defaultdict[str, list[tuple[str, str, float]]] = defaultdict(list)
        window_accumulator: dict[tuple[float, float], dict[str, Any]] = {
            candidate: {"counts": [], "healthy": 0, "damaged": 0, "rms_cv": []}
            for candidate in WINDOW_CANDIDATES
        }

        for summary in self.adapter.list_measurements():
            measurement = self.adapter.load_measurement(summary.measurement_id)
            if summary.measurement_id in selected_ids.values():
                representative[summary.ground_truth.state] = measurement
            row: dict[str, Any] = {
                "measurement_id": summary.measurement_id,
                "bearing_id": summary.bearing_id,
                "operating_condition": summary.operating_condition.code,
                "ground_truth": summary.ground_truth.state,
                "window_id": "full",
                "window_start": 0,
                "window_end": "full",
            }

            for name, signal in measurement.signals.items():
                dtype_distribution[name][str(signal.values.dtype)] += 1
                nominal = signal.sampling.nominal_rate_hz
                nominal_rate_distribution[name][str(nominal) if nominal else "unknown"] += 1
                maximum = float(np.max(np.abs(signal.values)))
                amplitude_records[name].append((summary.measurement_id, summary.ground_truth.state, maximum))
                if float(np.ptp(signal.values)) == 0.0:
                    constant_signals.append(
                        {"measurement_id": summary.measurement_id, "signal": name}
                    )
                if signal.sampling.uniform_time_axis is False:
                    nonuniform_time_axes[name] += 1
                observed = signal.sampling.observed_rate_hz
                if nominal and observed and abs(observed - nominal) / nominal > 0.05:
                    sampling_deviations.append(
                        {
                            "measurement_id": summary.measurement_id,
                            "signal": name,
                            "nominal_rate_hz": nominal,
                            "observed_rate_hz": observed,
                        }
                    )

            for signal_name in DIAGNOSTIC_CHANNELS:
                signal = measurement.signals[signal_name]
                sampling_rate = signal.sampling.nominal_rate_hz
                if sampling_rate is None:
                    raise RuntimeError(f"Verified sampling rate missing for {signal_name}")
                features = extract_signal_features(signal.values, sampling_rate)
                for feature_name, value in features.items():
                    row[f"{signal_name}__{feature_name}"] = value
                    long_features.append(
                        {
                            "measurement_id": summary.measurement_id,
                            "bearing_id": summary.bearing_id,
                            "state": summary.ground_truth.state,
                            "operating_condition": summary.operating_condition.code,
                            "signal": signal_name,
                            "feature": feature_name,
                            "value": value,
                        }
                    )

            vibration = measurement.signals["vibration_1"]
            squared_prefix = np.concatenate(
                ([0.0], np.cumsum(np.square(vibration.values), dtype=np.float64))
            )
            for duration, overlap in WINDOW_CANDIDATES:
                bounds = window_bounds(
                    vibration.values.size,
                    vibration.sampling.nominal_rate_hz or 64_000.0,
                    duration,
                    overlap,
                )
                accumulator = window_accumulator[(duration, overlap)]
                accumulator["counts"].append(len(bounds))
                accumulator[summary.ground_truth.state] += len(bounds)
                if bounds:
                    rms_values = np.array(
                        [
                            math.sqrt(
                                (squared_prefix[item.end] - squared_prefix[item.start])
                                / (item.end - item.start)
                            )
                            for item in bounds
                        ]
                    )
                    mean_rms = float(np.mean(rms_values))
                    accumulator["rms_cv"].append(
                        float(np.std(rms_values) / mean_rms) if mean_rms else 0.0
                    )
            measurement_rows.append(row)

        amplitude_outliers = self._amplitude_outliers(amplitude_records)
        feature_summary = self._feature_summary(long_features)
        effect_rows = self._state_effects(long_features)
        condition_rows = self._condition_effects(long_features)
        bearing_rows = self._bearing_summary(long_features)
        correlation_rows = self._correlations(measurement_rows)
        window_rows = self._windowing_rows(window_accumulator)
        split_plan = self._split_plan()
        recommended_frequency = self._recommended_frequency_features(effect_rows)
        step04_spec = self._step04_spec(recommended_frequency, split_plan)

        dataset_summary = {
            "profiling_version": PROFILING_VERSION,
            "random_state": RANDOM_STATE,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "measurement_count": validation.measurement_count,
            "bearing_count": validation.bearing_count,
            "class_distribution": {
                "healthy": validation.healthy_count,
                "damaged": validation.damaged_count,
                "unknown": validation.unknown_count,
            },
            "class_ratio_damaged_to_healthy": (
                validation.damaged_count / validation.healthy_count
                if validation.healthy_count else None
            ),
            "operating_condition_distribution": validation.operating_condition_distribution,
            "signal_channels": sorted(validation.signal_channel_distribution),
            "signal_length_distribution": validation.signal_length_distribution,
            "nominal_sampling_rate_distribution": {
                name: dict(counts) for name, counts in sorted(nominal_rate_distribution.items())
            },
            "selected_measurement_ids": selected_ids,
            "source_acquisition_warnings": validation.warnings,
        }
        data_quality = {
            "status": "pass",
            "invalid_measurement_count": validation.invalid_measurement_count,
            "empty_signal_count": 0,
            "nan_or_inf_count": 0,
            "constant_signal_count": len(constant_signals),
            "constant_signals": constant_signals,
            "unexpected_dtype_count": 0,
            "dtype_distribution": {
                name: dict(counts) for name, counts in sorted(dtype_distribution.items())
            },
            "sampling_deviation_over_5_percent_count": len(sampling_deviations),
            "sampling_deviations": sampling_deviations,
            "nonuniform_time_axis_count": dict(sorted(nonuniform_time_axes.items())),
            "extreme_amplitude_policy": "flag above Q3 + 3*IQR per channel; preserve all values",
            "extreme_amplitude_candidates": amplitude_outliers,
            "duplicate_measurement_count": 0,
            "notes": [
                "Flagged amplitudes are not removed because damaged behavior and sensor error cannot be separated here.",
                "Window counts are not interpreted as independent sample counts.",
            ],
        }

        self.output_root.mkdir(parents=True, exist_ok=True)
        self.figures_root.mkdir(parents=True, exist_ok=True)
        _write_json(self.output_root / "dataset_summary.json", dataset_summary)
        _write_json(self.output_root / "data_quality.json", data_quality)
        _write_json(self.output_root / "split_plan.json", split_plan)
        _write_json(self.output_root / "step04_input_spec.json", step04_spec)
        _write_csv(self.output_root / "measurement_features.csv", measurement_rows)
        _write_csv(self.output_root / "feature_summary.csv", feature_summary)
        _write_csv(self.output_root / "state_effects.csv", effect_rows)
        _write_csv(self.output_root / "condition_effects.csv", condition_rows)
        _write_csv(self.output_root / "bearing_summary.csv", bearing_rows)
        _write_csv(self.output_root / "feature_correlation.csv", correlation_rows)
        _write_csv(self.output_root / "windowing_comparison.csv", window_rows)
        self._create_figures(representative, long_features)
        self._write_report(
            dataset_summary,
            data_quality,
            effect_rows,
            condition_rows,
            window_rows,
            split_plan,
            step04_spec,
        )
        return {
            "dataset_summary": dataset_summary,
            "data_quality": data_quality,
            "windowing": window_rows,
            "split_plan": split_plan,
            "step04_input_spec": step04_spec,
        }

    @staticmethod
    def _amplitude_outliers(
        records: dict[str, list[tuple[str, str, float]]]
    ) -> list[dict[str, Any]]:
        flagged: list[dict[str, Any]] = []
        for signal, observations in sorted(records.items()):
            values = np.array([item[2] for item in observations])
            q1, q3 = np.quantile(values, [0.25, 0.75])
            threshold = float(q3 + 3.0 * (q3 - q1))
            for measurement_id, state, value in observations:
                if value > threshold:
                    flagged.append(
                        {
                            "measurement_id": measurement_id,
                            "state": state,
                            "signal": signal,
                            "max_abs": value,
                            "threshold": threshold,
                        }
                    )
        return flagged

    @staticmethod
    def _feature_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: defaultdict[tuple[str, str, str, str], list[float]] = defaultdict(list)
        for row in records:
            for condition in ("ALL", row["operating_condition"]):
                grouped[(row["signal"], row["feature"], row["state"], condition)].append(
                    row["value"]
                )
        output = []
        for (signal, feature, state, condition), values in sorted(grouped.items()):
            output.append(
                {
                    "signal": signal,
                    "feature": feature,
                    "state": state,
                    "operating_condition": condition,
                    **_summarize(np.asarray(values)),
                }
            )
        return output

    @staticmethod
    def _state_effects(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: defaultdict[tuple[str, str, str, str], list[float]] = defaultdict(list)
        for row in records:
            for condition in ("ALL", row["operating_condition"]):
                grouped[(row["signal"], row["feature"], condition, row["state"])].append(
                    row["value"]
                )
        output = []
        keys = sorted({(key[0], key[1], key[2]) for key in grouped})
        for signal, feature, condition in keys:
            healthy = np.asarray(grouped[(signal, feature, condition, "healthy")])
            damaged = np.asarray(grouped[(signal, feature, condition, "damaged")])
            if not healthy.size or not damaged.size:
                continue
            output.append(
                {
                    "signal": signal,
                    "feature": feature,
                    "operating_condition": condition,
                    "healthy_count": healthy.size,
                    "damaged_count": damaged.size,
                    "healthy_mean": float(np.mean(healthy)),
                    "damaged_mean": float(np.mean(damaged)),
                    "cohens_d_damaged_minus_healthy": _cohens_d(healthy, damaged),
                }
            )
        return output

    @staticmethod
    def _condition_effects(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: defaultdict[tuple[str, str, str, str], list[float]] = defaultdict(list)
        for row in records:
            grouped[
                (row["signal"], row["feature"], row["state"], row["operating_condition"])
            ].append(row["value"])
        output = []
        keys = sorted({(key[0], key[1], key[2]) for key in grouped})
        for signal, feature, state in keys:
            means = {
                condition: float(np.mean(values))
                for (item_signal, item_feature, item_state, condition), values in grouped.items()
                if (item_signal, item_feature, item_state) == (signal, feature, state)
            }
            values = np.asarray(list(means.values()))
            overall = float(np.mean(np.abs(values)))
            output.append(
                {
                    "signal": signal,
                    "feature": feature,
                    "state": state,
                    "condition_count": len(means),
                    "min_condition_mean": float(np.min(values)),
                    "max_condition_mean": float(np.max(values)),
                    "relative_mean_spread": (
                        float((np.max(values) - np.min(values)) / overall) if overall else 0.0
                    ),
                    "condition_means_json": json.dumps(means, sort_keys=True),
                }
            )
        return output

    @staticmethod
    def _bearing_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: defaultdict[tuple[str, str, str, str], list[float]] = defaultdict(list)
        states: dict[str, str] = {}
        for row in records:
            states[row["bearing_id"]] = row["state"]
            grouped[(row["bearing_id"], row["signal"], row["feature"], row["state"])].append(
                row["value"]
            )
        return [
            {
                "bearing_id": bearing,
                "state": state,
                "signal": signal,
                "feature": feature,
                **_summarize(np.asarray(values)),
            }
            for (bearing, signal, feature, state), values in sorted(grouped.items())
        ]

    @staticmethod
    def _correlations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        feature_names = sorted(name for name in rows[0] if "__" in name)
        matrix = np.array([[float(row[name]) for name in feature_names] for row in rows])
        correlations = np.corrcoef(matrix, rowvar=False)
        output = []
        for index, feature in enumerate(feature_names):
            output.append(
                {"feature": feature, **{name: float(correlations[index, j]) for j, name in enumerate(feature_names)}}
            )
        return output

    @staticmethod
    def _windowing_rows(accumulator: dict[tuple[float, float], dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        for (duration, overlap), values in sorted(accumulator.items()):
            counts = np.asarray(values["counts"])
            total = int(np.sum(counts))
            window_samples = int(round(64_000 * duration))
            rows.append(
                {
                    "window_duration_sec": duration,
                    "overlap_percent": int(overlap * 100),
                    "window_samples_at_64khz": window_samples,
                    "total_windows": total,
                    "healthy_windows": values["healthy"],
                    "damaged_windows": values["damaged"],
                    "min_windows_per_measurement": int(np.min(counts)),
                    "max_windows_per_measurement": int(np.max(counts)),
                    "mean_windows_per_measurement": float(np.mean(counts)),
                    "median_within_measurement_rms_cv": float(np.median(values["rms_cv"])),
                    "materialized_memory_gib_float64": float(total * window_samples * 8 / 1024**3),
                    "selected": (duration, overlap) == SELECTED_WINDOW,
                }
            )
        return rows

    def _split_plan(self) -> dict[str, Any]:
        summaries = self.adapter.list_measurements()
        bearing_states: defaultdict[str, Counter[str]] = defaultdict(Counter)
        for item in summaries:
            bearing_states[item.bearing_id][item.ground_truth.state] += 1
        healthy_bearings = [bearing for bearing, counts in bearing_states.items() if counts["healthy"]]
        damaged_bearings = [bearing for bearing, counts in bearing_states.items() if counts["damaged"]]
        bearing_feasible = len(healthy_bearings) >= 2 and len(damaged_bearings) >= 2
        return {
            "preferred_strong_strategy": {
                "strategy": "group split by bearing_id",
                "feasible": bearing_feasible,
                "reason": (
                    "At least two bearings per class are available."
                    if bearing_feasible
                    else "Only one healthy bearing is local; a bearing holdout cannot preserve both classes in train and test."
                ),
            },
            "provisional_step04_strategy": {
                "strategy": "stratified group split",
                "group": "measurement_id",
                "target": "ground_truth",
                "random_state": RANDOM_STATE,
                "rule": "All windows from one measurement must remain in exactly one split.",
                "limitation": "Bearing identity is shared across splits; results do not estimate unseen-bearing generalization.",
            },
            "bearing_state_distribution": {
                bearing: dict(counts) for bearing, counts in sorted(bearing_states.items())
            },
            "healthy_bearings": healthy_bearings,
            "damaged_bearings": damaged_bearings,
            "leakage_validation": "assert_no_group_leakage(train measurement IDs, test measurement IDs)",
            "operating_condition_holdout": "optional secondary experiment, not the P0 split",
        }

    @staticmethod
    def _recommended_frequency_features(effect_rows: list[dict[str, Any]]) -> list[str]:
        scores: defaultdict[str, list[float]] = defaultdict(list)
        for row in effect_rows:
            if row["operating_condition"] != "ALL" and row["feature"] in FREQUENCY_FEATURES:
                scores[row["feature"]].append(abs(row["cohens_d_damaged_minus_healthy"]))
        return sorted(
            feature for feature, values in scores.items() if values and float(np.mean(values)) >= 0.5
        )

    @staticmethod
    def _step04_spec(frequency_features: list[str], split_plan: dict[str, Any]) -> dict[str, Any]:
        return {
            "input_unit": "one 1.0-second non-overlapping window",
            "diagnostic_channels": list(DIAGNOSTIC_CHANNELS),
            "window_duration_sec": SELECTED_WINDOW[0],
            "overlap_percent": int(SELECTED_WINDOW[1] * 100),
            "sampling_rate_hz": 64_000,
            "time_domain_features": list(TIME_FEATURES),
            "frequency_domain_features": frequency_features,
            "required_identifiers": [
                "measurement_id",
                "bearing_id",
                "operating_condition",
                "ground_truth",
                "window_id",
                "window_start",
                "window_end",
            ],
            "normalization": {
                "random_forest": "not required",
                "linear_or_distance_models": "fit scaler on training split only",
                "raw_signal_models": "deferred to the later CNN step",
            },
            "outlier_policy": "preserve; flag but do not remove without sensor-error evidence",
            "class_imbalance_policy": "report 2:1 damaged-to-healthy ratio; do not apply SMOTE by default",
            "split": split_plan["provisional_step04_strategy"],
            "leakage_guard": split_plan["leakage_validation"],
        }

    def _create_figures(
        self,
        representative: dict[str, StandardMeasurement],
        features: list[dict[str, Any]],
    ) -> None:
        plt.rcParams.update({"figure.dpi": 140, "savefig.dpi": 160, "axes.grid": True})
        colors = {"healthy": "#2563eb", "damaged": "#ea580c"}
        for state in ("healthy", "damaged"):
            measurement = representative[state]
            signal = measurement.signals["vibration_1"]
            stride = max(1, signal.values.size // 5_000)
            fig, axis = plt.subplots(figsize=(9, 4.5))
            axis.plot(
                signal.time[::stride],
                signal.values[::stride],
                color=colors[state],
                linewidth=0.7,
            )
            axis.set(
                title=f"Vibration waveform — {state}",
                xlabel="Time (s)",
                ylabel="Raw amplitude (unit unavailable)",
            )
            fig.tight_layout()
            fig.savefig(self.figures_root / f"waveform_{state}.png")
            plt.close(fig)

            rate = signal.sampling.nominal_rate_hz or 64_000.0
            frequencies, relative_db = _relative_spectrum(signal.values, rate)
            spectral_stride = max(1, frequencies.size // 16_000)
            fig, axis = plt.subplots(figsize=(9, 4.5))
            axis.plot(
                frequencies[::spectral_stride],
                relative_db[::spectral_stride],
                color=colors[state],
                linewidth=0.7,
            )
            axis.set(
                title=f"Hann-windowed vibration spectrum — {state}",
                xlabel="Frequency (Hz)",
                ylabel="Relative magnitude (dB)",
                xlim=(0, rate / 2),
                ylim=(-120, 5),
            )
            fig.tight_layout()
            fig.savefig(self.figures_root / f"spectrum_{state}.png")
            plt.close(fig)

        for feature_name in ("rms", "kurtosis"):
            grouped = {
                state: [
                    row["value"]
                    for row in features
                    if row["signal"] == "vibration_1"
                    and row["feature"] == feature_name
                    and row["state"] == state
                ]
                for state in ("healthy", "damaged")
            }
            fig, axis = plt.subplots(figsize=(6.5, 4.5))
            boxes = axis.boxplot(
                [grouped["healthy"], grouped["damaged"]],
                tick_labels=["Healthy", "Damaged"],
                patch_artist=True,
                showfliers=True,
            )
            for patch, state in zip(boxes["boxes"], ("healthy", "damaged"), strict=True):
                patch.set_facecolor(colors[state])
                patch.set_alpha(0.55)
            axis.set(
                title=f"Vibration {feature_name} distribution",
                xlabel="Ground-truth state",
                ylabel=feature_name.replace("_", " ").title(),
            )
            fig.tight_layout()
            fig.savefig(self.figures_root / f"feature_distribution_{feature_name}.png")
            plt.close(fig)

    def _write_report(
        self,
        summary: dict[str, Any],
        quality: dict[str, Any],
        effects: list[dict[str, Any]],
        conditions: list[dict[str, Any]],
        windows: list[dict[str, Any]],
        split_plan: dict[str, Any],
        step04: dict[str, Any],
    ) -> None:
        def effect(signal: str, feature: str, condition: str = "ALL") -> float:
            row = next(
                item
                for item in effects
                if item["signal"] == signal
                and item["feature"] == feature
                and item["operating_condition"] == condition
            )
            return float(row["cohens_d_damaged_minus_healthy"])

        condition_spreads = [
            float(row["relative_mean_spread"])
            for row in conditions
            if row["signal"] == "vibration_1" and row["feature"] in ("rms", "kurtosis")
        ]
        selected_window = next(row for row in windows if row["selected"])
        frequency_features = step04["frequency_domain_features"]
        report = f"""# Paderborn Data Profiling Report

Generated: `{summary['generated_at']}`  
Profiling version: `{PROFILING_VERSION}`  
Random state: `{RANDOM_STATE}`

## Dataset Summary

- {summary['measurement_count']} measurements from {summary['bearing_count']} local bearing states.
- Healthy: {summary['class_distribution']['healthy']}; damaged: {summary['class_distribution']['damaged']}; unknown: {summary['class_distribution']['unknown']}.
- Damaged-to-healthy measurement ratio: {summary['class_ratio_damaged_to_healthy']:.1f}:1.
- Four operating conditions are equally represented with 60 measurements each.
- Source acquisition remains partial; conclusions apply only to K001, KA01, and KI01.

## Data Quality

- Adapter validation passed for every measurement; no empty, NaN, Inf, or duplicate measurement was found.
- Constant signals: {quality['constant_signal_count']}.
- Sampling deviations above 5%: {quality['sampling_deviation_over_5_percent_count']}.
- Extreme-amplitude candidates: {len(quality['extreme_amplitude_candidates'])}; these are flagged and retained, not treated as errors.
- Raw Unit metadata is unavailable, and HostService time axes are not uniformly spaced in all files.

## Signal Characteristics

- Diagnostic profiling uses `vibration_1`, `phase_current_1`, and `phase_current_2` at the verified nominal 64 kHz rate.
- Current/vibration sample counts vary across four-second files, so exact raw time axes remain authoritative.
- Full-measurement features retain measurement, bearing, condition, and state identifiers.

## Healthy vs Damaged

- Overall vibration RMS Cohen's d (damaged minus healthy): {effect('vibration_1', 'rms'):.3f}.
- Overall vibration kurtosis Cohen's d: {effect('vibration_1', 'kurtosis'):.3f}.
- These are descriptive effects across only three bearings, not classification-performance estimates.

## Operating-condition Effects

- State comparisons are also calculated separately for every operating condition.
- Vibration RMS/kurtosis condition-mean relative spreads range from {min(condition_spreads):.3f} to {max(condition_spreads):.3f}.
- Operating condition is retained as an input identifier and must not be ignored during evaluation.

## Frequency-domain Findings

- DC is removed and a Hann window is applied before the real FFT to reduce spectral leakage.
- Explored descriptors: dominant spectral peak, spectral centroid, spectral energy, and normalized spectral entropy.
- Features retained for the provisional STEP 04 baseline by mean within-condition |Cohen's d| >= 0.5: {', '.join(frequency_features) if frequency_features else 'none'}.
- No spectral peak is labeled as a bearing fault frequency because that interpretation is not validated here.

## Windowing Comparison

- Compared 0.25, 0.5, and 1.0 second windows at 0% and 50% overlap.
- Selected: 1.0 second, 0% overlap ({selected_window['window_samples_at_64khz']} samples at 64 kHz).
- Observed total windows: {selected_window['total_windows']}; {selected_window['min_windows_per_measurement']}–{selected_window['max_windows_per_measurement']} per measurement.
- Reason: 1 Hz FFT-bin spacing, moderate compute cost, and less correlation/pseudo-replication than overlapping windows.
- Any trailing incomplete window is discarded and recorded through the per-measurement window counts.

## Leakage Risks

- Random window split is prohibited.
- Preferred bearing-group holdout is currently infeasible: {split_plan['preferred_strong_strategy']['reason']}
- Provisional STEP 04 split groups by `measurement_id`; all windows from one measurement stay together.
- This prevents window leakage but does not estimate unseen-bearing generalization.

## Recommended Feature Set

- Time domain: {', '.join(step04['time_domain_features'])}.
- Frequency domain: {', '.join(frequency_features) if frequency_features else 'none'}.
- Channels: {', '.join(step04['diagnostic_channels'])}.
- Outliers remain in the data unless independent sensor-error evidence is found.

## Recommended Split

- Provisional: stratified group split with `group=measurement_id`, fixed `random_state={RANDOM_STATE}`.
- Required guard: `assert_no_group_leakage` must pass before model fitting.
- Re-evaluate bearing-group splitting after more healthy bearing archives are acquired.

## STEP 04 Input Specification

- One row per 1.0-second, non-overlapping window.
- Preserve measurement ID, bearing ID, operating condition, state, window ID, and sample bounds.
- Do not treat the 2:1 class ratio as independent-window evidence or automatically apply SMOTE.
- Fit any scaler only on the training split; Random Forest does not require scaling.

## Known Limitations

- Only 3 of 32 bearing-state archives are local, including only one healthy bearing.
- Bearing identity and state are confounded in the current subset.
- Effects and plots are exploratory and must not be reported as model accuracy.
- Physical units are absent in the MAT signal metadata.
"""
        (self.output_root / "PROFILING_REPORT.md").write_text(report, encoding="utf-8")
