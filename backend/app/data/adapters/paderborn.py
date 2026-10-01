"""Adapter for the observed Paderborn Bearing DataCenter MATLAB structure."""

from __future__ import annotations

import json
import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable

import numpy as np
from scipy.io import loadmat

from app.data.adapters.base import SensorDatasetAdapter
from app.data.errors import (
    DatasetNotFoundError,
    InvalidMeasurementError,
    MeasurementNotFoundError,
    UnsupportedMatFormatError,
)
from app.data.models import (
    DatasetValidationResult,
    GroundTruth,
    InvalidMeasurement,
    MeasurementSummary,
    OperatingCondition,
    SamplingMetadata,
    SignalSeries,
    StandardMeasurement,
)


logger = logging.getLogger(__name__)

SOURCE = "paderborn-bearing-datacenter"
EQUIPMENT_ID = "paderborn-bearing-test-rig"
FILE_PATTERN = re.compile(
    r"^(?P<condition>N\d+_M\d+_F\d+)_(?P<bearing>K[A-Z]?\d+)_(?P<run>\d+)\.mat$"
)

# Values are copied from the acquired official operating-condition page.
OPERATING_CONDITIONS: dict[str, OperatingCondition] = {
    "N15_M07_F10": OperatingCondition(
        code="N15_M07_F10", rpm=1500, load_torque_nm=0.7, radial_force_n=1000
    ),
    "N09_M07_F10": OperatingCondition(
        code="N09_M07_F10", rpm=900, load_torque_nm=0.7, radial_force_n=1000
    ),
    "N15_M01_F10": OperatingCondition(
        code="N15_M01_F10", rpm=1500, load_torque_nm=0.1, radial_force_n=1000
    ),
    "N15_M07_F04": OperatingCondition(
        code="N15_M07_F04", rpm=1500, load_torque_nm=0.7, radial_force_n=400
    ),
}

# Only acquired and inspected fact sheets are mapped. Other bearing IDs remain unknown.
GROUND_TRUTH: dict[str, GroundTruth] = {
    "K001": GroundTruth(
        state="healthy",
        evidence_reference="data/paderborn/docs/K001/K001.pdf",
    ),
    "KA01": GroundTruth(
        state="damaged",
        fault_type="artificial",
        damage_location="outer_ring_raceway",
        damage_mechanism="EDM machining",
        evidence_reference="data/paderborn/docs/KA01/KA01.pdf",
    ),
    "KI01": GroundTruth(
        state="damaged",
        fault_type="artificial",
        damage_location="inner_ring_raceway",
        damage_mechanism=None,
        evidence_reference="data/paderborn/docs/KI01/KI01.pdf",
    ),
}

OFFICIAL_HIGH_RATE_CHANNELS = {"phase_current_1", "phase_current_2", "vibration_1"}


@dataclass(frozen=True, slots=True)
class _IndexEntry:
    summary: MeasurementSummary
    path: Path


def _sequence(value: Any) -> list[Any]:
    if isinstance(value, np.ndarray):
        return list(value.reshape(-1))
    return [value]


def _scalar_text(value: Any) -> str | None:
    if isinstance(value, np.ndarray):
        if value.size == 0:
            return None
        value = value.reshape(-1)[0]
    text = str(value).strip()
    return text or None


def _nominal_rate(channel_name: str, raster: str) -> float | None:
    if channel_name in OFFICIAL_HIGH_RATE_CHANNELS:
        return 64_000.0
    match = re.fullmatch(r".*?(?P<value>\d+(?:\.\d+)?)kHz", raster, re.IGNORECASE)
    if match:
        return float(match.group("value")) * 1_000.0
    match = re.fullmatch(r".*?(?P<value>\d+(?:\.\d+)?)Hz", raster, re.IGNORECASE)
    if match:
        return float(match.group("value"))
    return None


class PaderbornDatasetAdapter(SensorDatasetAdapter):
    """Discover and lazily load verified Paderborn MATLAB measurements."""

    def __init__(self, dataset_root: Path | str):
        self.dataset_root = Path(dataset_root).expanduser().resolve()
        if not self.dataset_root.is_dir():
            raise DatasetNotFoundError(f"Paderborn dataset root not found: {self.dataset_root}")
        started = perf_counter()
        self._index = self._build_index()
        self.index_build_seconds = perf_counter() - started
        logger.info(
            "Paderborn dataset initialized root=%s measurements=%d index_seconds=%.4f",
            self.dataset_root,
            len(self._index),
            self.index_build_seconds,
        )

    @staticmethod
    def _measurement_id(bearing_id: str, condition: str, run_index: int) -> str:
        return f"paderborn:{bearing_id}:{condition}:{run_index:02d}"

    def _build_index(self) -> dict[str, _IndexEntry]:
        index: dict[str, _IndexEntry] = {}
        mat_paths = sorted(self.dataset_root.rglob("*.mat"))
        if not mat_paths:
            raise DatasetNotFoundError(f"No MAT files found below: {self.dataset_root}")
        for path in mat_paths:
            match = FILE_PATTERN.fullmatch(path.name)
            if not match:
                logger.warning("Skipping unrecognized MAT filename: %s", path)
                continue
            condition_code = match.group("condition")
            bearing_id = match.group("bearing")
            run_index = int(match.group("run"))
            measurement_id = self._measurement_id(bearing_id, condition_code, run_index)
            if measurement_id in index:
                previous = index[measurement_id].path
                raise InvalidMeasurementError(
                    f"Duplicate measurement ID {measurement_id}: {previous} and {path}"
                )
            condition = OPERATING_CONDITIONS.get(
                condition_code, OperatingCondition(code=condition_code)
            )
            ground_truth = GROUND_TRUTH.get(
                bearing_id,
                GroundTruth(state="unknown"),
            )
            relative_path = path.relative_to(self.dataset_root).as_posix()
            summary = MeasurementSummary(
                measurement_id=measurement_id,
                equipment_id=EQUIPMENT_ID,
                source=SOURCE,
                bearing_id=bearing_id,
                operating_condition=condition,
                run_index=run_index,
                ground_truth=ground_truth,
                source_reference=relative_path,
            )
            index[measurement_id] = _IndexEntry(summary=summary, path=path)
        if not index:
            raise DatasetNotFoundError(
                f"No MAT files matched the observed Paderborn filename pattern below: {self.dataset_root}"
            )
        return dict(sorted(index.items()))

    def list_measurements(self) -> tuple[MeasurementSummary, ...]:
        return tuple(entry.summary for entry in self._index.values())

    def get_metadata(self, measurement_id: str) -> MeasurementSummary:
        return self._entry(measurement_id).summary

    def _entry(self, measurement_id: str) -> _IndexEntry:
        try:
            return self._index[measurement_id]
        except KeyError as exc:
            raise MeasurementNotFoundError(
                f"Measurement ID is not present in the internal index: {measurement_id}"
            ) from exc

    @staticmethod
    def _require_mat_v5(path: Path) -> None:
        with path.open("rb") as stream:
            header = stream.read(128)
        if not header.startswith(b"MATLAB 5.0 MAT-file"):
            raise UnsupportedMatFormatError(f"Unsupported MAT format: {path}")

    def load_measurement(self, measurement_id: str) -> StandardMeasurement:
        entry = self._entry(measurement_id)
        path = entry.path.resolve()
        try:
            path.relative_to(self.dataset_root)
        except ValueError as exc:
            raise InvalidMeasurementError(
                f"Indexed path escaped configured dataset root: {entry.summary.source_reference}"
            ) from exc
        if not path.is_file():
            raise InvalidMeasurementError(f"Source file is missing: {entry.summary.source_reference}")
        self._require_mat_v5(path)

        document = loadmat(path, squeeze_me=True, struct_as_record=False)
        keys = [key for key in document if not key.startswith("__")]
        if keys != [path.stem]:
            raise InvalidMeasurementError(
                f"Expected one top-level variable named {path.stem}; observed {keys}"
            )
        root = document[path.stem]
        root_fields = set(getattr(root, "_fieldnames", []))
        required_fields = {"Info", "X", "Y", "Description"}
        if not required_fields.issubset(root_fields):
            raise InvalidMeasurementError(
                f"Missing root fields in {entry.summary.source_reference}: "
                f"{sorted(required_fields - root_fields)}"
            )

        x_axes = _sequence(root.X)
        signals: dict[str, SignalSeries] = {}
        for raw_signal in _sequence(root.Y):
            signal_fields = set(getattr(raw_signal, "_fieldnames", []))
            required_signal_fields = {"Name", "Data", "Raster", "XIndex"}
            if not required_signal_fields.issubset(signal_fields):
                raise InvalidMeasurementError(
                    f"Missing signal fields in {entry.summary.source_reference}: "
                    f"{sorted(required_signal_fields - signal_fields)}"
                )
            channel_name = _scalar_text(getattr(raw_signal, "Name", None))
            raster = _scalar_text(getattr(raw_signal, "Raster", None))
            if not channel_name or not raster:
                raise InvalidMeasurementError(
                    f"Signal without Name/Raster in {entry.summary.source_reference}"
                )
            if channel_name in signals:
                raise InvalidMeasurementError(
                    f"Duplicate signal channel {channel_name} in {entry.summary.source_reference}"
                )
            try:
                x_index = int(np.asarray(getattr(raw_signal, "XIndex")).item()) - 1
                raw_axis = x_axes[x_index]
                if "Data" not in set(getattr(raw_axis, "_fieldnames", [])):
                    raise AttributeError("X axis has no Data field")
            except (AttributeError, IndexError, TypeError, ValueError) as exc:
                raise InvalidMeasurementError(
                    f"Invalid XIndex for {channel_name} in {entry.summary.source_reference}"
                ) from exc

            values = np.asarray(getattr(raw_signal, "Data"))
            time_axis = np.asarray(getattr(raw_axis, "Data"))
            if values.ndim != 1 or time_axis.ndim != 1:
                raise InvalidMeasurementError(
                    f"Expected one-dimensional arrays for {channel_name} in "
                    f"{entry.summary.source_reference}"
                )
            if values.size == 0 or values.size != time_axis.size:
                raise InvalidMeasurementError(
                    f"Signal/time length mismatch for {channel_name} in "
                    f"{entry.summary.source_reference}: {values.size}/{time_axis.size}"
                )
            if not np.issubdtype(values.dtype, np.number):
                raise InvalidMeasurementError(
                    f"Non-numeric signal {channel_name} in {entry.summary.source_reference}"
                )

            duration_sec: float | None = None
            observed_rate_hz: float | None = None
            uniform_time_axis: bool | None = None
            if time_axis.size > 1:
                differences = np.diff(time_axis.astype(np.float64, copy=False))
                duration = float(time_axis[-1] - time_axis[0])
                if duration > 0:
                    duration_sec = duration
                    observed_rate_hz = float((time_axis.size - 1) / duration)
                median_difference = float(np.median(differences))
                uniform_time_axis = bool(
                    median_difference > 0
                    and np.allclose(
                        differences,
                        median_difference,
                        rtol=1e-3,
                        atol=max(abs(median_difference) * 1e-6, 1e-12),
                    )
                )

            sampling = SamplingMetadata(
                raster=raster,
                nominal_rate_hz=_nominal_rate(channel_name, raster),
                observed_rate_hz=observed_rate_hz,
                sample_count=int(values.size),
                duration_sec=duration_sec,
                uniform_time_axis=uniform_time_axis,
            )
            raw_metadata = {
                "unit": _scalar_text(getattr(raw_signal, "Unit", None)),
                "device": _scalar_text(getattr(raw_signal, "Device", None)),
                "path": _scalar_text(getattr(raw_signal, "Path", None)),
                "x_index": x_index + 1,
                "down_sampling": _scalar_text(getattr(raw_signal, "DownSampling", None)),
            }
            signals[channel_name] = SignalSeries(
                name=channel_name,
                values=values,
                time=time_axis,
                sampling=sampling,
                raw_metadata=raw_metadata,
            )

        try:
            measurement_description = root.Description.Measurement
            measurement_id_in_file = int(np.asarray(root.Info.MeasurementID).item())
            recorded_at_raw = _scalar_text(root.Description.General.DateTime)
            measurement_duration_sec = float(
                np.asarray(measurement_description.Length).item()
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise InvalidMeasurementError(
                f"Invalid Info/Description metadata in {entry.summary.source_reference}"
            ) from exc
        metadata = {
            "mat_variable": path.stem,
            "measurement_id_in_file": measurement_id_in_file,
            "recorded_at_raw": recorded_at_raw,
            "measurement_duration_sec": measurement_duration_sec,
            "observed_root_fields": sorted(root_fields),
        }
        logger.debug("Loaded measurement=%s channels=%d", measurement_id, len(signals))
        return StandardMeasurement(summary=entry.summary, signals=signals, metadata=metadata)

    def validate(self) -> DatasetValidationResult:
        started = perf_counter()
        state_counts = Counter(summary.ground_truth.state for summary in self.list_measurements())
        condition_counts = Counter(
            summary.operating_condition.code for summary in self.list_measurements()
        )
        channel_counts: Counter[str] = Counter()
        channel_lengths: defaultdict[str, list[int]] = defaultdict(list)
        invalid: list[InvalidMeasurement] = []
        missing_metadata_count = 0

        for summary in self.list_measurements():
            if summary.ground_truth.state == "unknown":
                missing_metadata_count += 1
            errors: list[str] = []
            try:
                measurement = self.load_measurement(summary.measurement_id)
                if not measurement.signals:
                    errors.append("no signal channels")
                for name, signal in measurement.signals.items():
                    channel_counts[name] += 1
                    channel_lengths[name].append(signal.sampling.sample_count)
                    if not np.isfinite(signal.values).all():
                        errors.append(f"{name}: NaN or Inf detected")
                    if not np.isfinite(signal.time).all():
                        errors.append(f"{name}: non-finite time axis detected")
                    if signal.sampling.sample_count != signal.values.size:
                        errors.append(f"{name}: sample-count mismatch")
            except (
                OSError,
                AttributeError,
                IndexError,
                TypeError,
                ValueError,
                InvalidMeasurementError,
                UnsupportedMatFormatError,
            ) as exc:
                errors.append(str(exc))
            if errors:
                invalid.append(
                    InvalidMeasurement(
                        measurement_id=summary.measurement_id,
                        source_reference=summary.source_reference,
                        errors=errors,
                    )
                )

        warnings = self._acquisition_warnings()
        length_distribution = {
            name: {"count": len(lengths), "min": min(lengths), "max": max(lengths)}
            for name, lengths in sorted(channel_lengths.items())
        }
        elapsed = perf_counter() - started
        return DatasetValidationResult(
            status="pass" if not invalid else "fail",
            measurement_count=len(self._index),
            bearing_count=len({summary.bearing_id for summary in self.list_measurements()}),
            healthy_count=state_counts["healthy"],
            damaged_count=state_counts["damaged"],
            unknown_count=state_counts["unknown"],
            operating_condition_distribution=dict(sorted(condition_counts.items())),
            signal_channel_distribution=dict(sorted(channel_counts.items())),
            signal_length_distribution=length_distribution,
            missing_metadata_count=missing_metadata_count,
            invalid_measurement_count=len(invalid),
            invalid_measurements=invalid,
            warnings=warnings,
            index_build_seconds=self.index_build_seconds,
            validation_seconds=elapsed,
        )

    def _acquisition_warnings(self) -> list[str]:
        inventory_path = self.dataset_root / "metadata/dataset_files.json"
        if not inventory_path.is_file():
            return []
        try:
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            present = int(inventory["present_archive_count"])
            expected = int(inventory["expected_archive_count"])
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return ["Dataset acquisition inventory could not be read."]
        if present < expected:
            return [
                f"Dataset acquisition is partial: {present}/{expected} bearing-state archives are present."
            ]
        return []

    def inspection_summary(self) -> dict[str, Any]:
        """Return a bounded, serializable inspection summary without raw signals."""

        paths = [path for path in self.dataset_root.rglob("*") if path.is_file()]
        extensions = Counter(path.suffix.lower() or "[none]" for path in paths)
        measurements = self.list_measurements()
        representative = self.load_measurement(measurements[0].measurement_id)
        return {
            "dataset_root": "data/paderborn",
            "file_count": len(paths),
            "mat_file_count": len(self._index),
            "file_type_distribution": dict(sorted(extensions.items())),
            "observed_directory_pattern": "raw/extracted/{bearing_id}/{condition}_{bearing_id}_{run_index}.mat",
            "observed_filename_pattern": FILE_PATTERN.pattern,
            "mat_format": "MATLAB v5 little-endian",
            "observed_root_keys": representative.metadata["observed_root_fields"],
            "signal_candidates": list(representative.signals),
            "metadata_candidates": [
                "bearing_id",
                "operating_condition",
                "run_index",
                "measurement_id_in_file",
                "recorded_at_raw",
                "measurement_duration_sec",
            ],
            "sampling_info": {
                name: signal.sampling.model_dump(mode="json")
                for name, signal in representative.signals.items()
            },
            "bearing_ids": sorted({item.bearing_id for item in measurements}),
            "operating_conditions": sorted(
                {item.operating_condition.code for item in measurements}
            ),
            "unknown_fields": [
                "Signal Unit fields are empty in the inspected MAT files.",
                "Fault taxonomy is unknown for bearing IDs without an acquired fact sheet.",
                "HostService time-axis spacing and sample counts vary by file; raw time axes are preserved.",
            ],
        }
