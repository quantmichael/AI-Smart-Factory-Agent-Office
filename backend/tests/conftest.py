from pathlib import Path

import numpy as np
import pytest
from scipy.io import savemat

from app.data.adapters.base import SensorDatasetAdapter
from app.data.models import (
    DatasetValidationResult,
    GroundTruth,
    MeasurementSummary,
    OperatingCondition,
    SamplingMetadata,
    SignalSeries,
    StandardMeasurement,
)


def _write_measurement(path: Path, measurement_id: int) -> None:
    mechanical_time = np.linspace(0.0, 4.0, 5)
    high_rate_time = np.linspace(0.0, 4.0, 9)
    temperature_time = np.array([0.0, 4.0])
    x_axes = np.array(
        [
            {"Name": "", "Type": 4, "Data": mechanical_time, "Unit": "", "Raster": "Mech_4kHz"},
            {"Name": "", "Type": 4, "Data": high_rate_time, "Unit": "", "Raster": "HostService"},
            {"Name": "", "Type": 4, "Data": temperature_time, "Unit": "", "Raster": "Temp_1Hz"},
        ],
        dtype=object,
    )

    def signal(name: str, values: np.ndarray, raster: str, x_index: int) -> dict[str, object]:
        return {
            "Name": name,
            "Type": 4,
            "Data": values,
            "Unit": "",
            "Raster": raster,
            "Device": "Platform",
            "XIndex": x_index,
            "DownSampling": 1,
            "Path": "Model Root/Einggangssignal",
        }

    y_signals = np.array(
        [
            signal("force", np.full(5, 1000.0), "Mech_4kHz", 1),
            signal("phase_current_1", np.arange(9, dtype=float), "HostService", 2),
            signal("phase_current_2", np.arange(9, dtype=float) * -1, "HostService", 2),
            signal("speed", np.full(5, 1500.0), "Mech_4kHz", 1),
            signal("temp_2_bearing_module", np.array([45.0, 46.0]), "Temp_1Hz", 3),
            signal("torque", np.full(5, 0.7), "Mech_4kHz", 1),
            signal("vibration_1", np.sin(np.arange(9, dtype=float)), "HostService", 2),
        ],
        dtype=object,
    )
    document = {
        "Info": {"RevisionMajor": 2, "RevisionMinor": 1, "MeasurementID": measurement_id},
        "X": x_axes,
        "Y": y_signals,
        "Description": {
            "General": {"User": "test", "DateTime": "01.01.2026 00:00:00", "Origin": "test"},
            "Recording": {"StartCondition": "None", "StopCondition": "Time limit: 4.000000"},
            "Measurement": {
                "XAxisOffset": 0,
                "Length": 4,
                "StartTimestamp": 0,
                "StopTimestamp": 4,
            },
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    savemat(path, {path.stem: document})


@pytest.fixture
def paderborn_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "paderborn"
    _write_measurement(
        root / "raw/extracted/K001/N15_M07_F10_K001_1.mat",
        measurement_id=1,
    )
    _write_measurement(
        root / "raw/extracted/KA01/N15_M07_F04_KA01_2.mat",
        measurement_id=2,
    )
    return root


class SyntheticMLAdapter(SensorDatasetAdapter):
    def __init__(self) -> None:
        self.measurements: dict[str, StandardMeasurement] = {}
        for index, state in enumerate(("healthy", "healthy", "damaged", "damaged"), start=1):
            measurement_id = f"synthetic:{state}:{index}"
            summary = MeasurementSummary(
                measurement_id=measurement_id,
                equipment_id="synthetic-bearing-rig",
                source="synthetic-test",
                bearing_id=f"B{index}",
                operating_condition=OperatingCondition(code=f"C{index % 2}"),
                run_index=index,
                ground_truth=GroundTruth(state=state),
                source_reference=f"fixture-{index}",
            )
            time = np.arange(128, dtype=float) / 64.0
            amplitude = 1.0 if state == "healthy" else 4.0
            base = amplitude * np.sin(2 * np.pi * (5 + index) * time)
            sampling = SamplingMetadata(
                raster="synthetic",
                nominal_rate_hz=64.0,
                observed_rate_hz=64.0,
                sample_count=128,
                duration_sec=2.0,
                uniform_time_axis=True,
            )
            signals = {
                name: SignalSeries(
                    name=name,
                    values=base + offset,
                    time=time,
                    sampling=sampling,
                    raw_metadata={},
                )
                for name, offset in (
                    ("vibration_1", 0.0),
                    ("phase_current_1", 0.1),
                    ("phase_current_2", -0.1),
                )
            }
            self.measurements[measurement_id] = StandardMeasurement(
                summary=summary,
                signals=signals,
                metadata={},
            )

    def list_measurements(self):
        return tuple(item.summary for item in self.measurements.values())

    def load_measurement(self, measurement_id: str):
        return self.measurements[measurement_id]

    def get_metadata(self, measurement_id: str):
        return self.measurements[measurement_id].summary

    def validate(self):
        return DatasetValidationResult(
            status="pass",
            measurement_count=4,
            bearing_count=4,
            healthy_count=2,
            damaged_count=2,
            unknown_count=0,
            operating_condition_distribution={"C0": 2, "C1": 2},
            signal_channel_distribution={
                "vibration_1": 4,
                "phase_current_1": 4,
                "phase_current_2": 4,
            },
            signal_length_distribution={},
            missing_metadata_count=0,
            invalid_measurement_count=0,
            invalid_measurements=[],
            warnings=[],
            index_build_seconds=0,
            validation_seconds=0,
        )


@pytest.fixture
def ml_adapter() -> SyntheticMLAdapter:
    return SyntheticMLAdapter()


@pytest.fixture
def ml_input_spec() -> dict[str, object]:
    return {
        "diagnostic_channels": ["vibration_1", "phase_current_1", "phase_current_2"],
        "window_duration_sec": 1.0,
        "overlap_percent": 0,
        "time_domain_features": [
            "mean",
            "std",
            "rms",
            "peak",
            "peak_to_peak",
            "crest_factor",
            "skewness",
            "kurtosis",
        ],
        "frequency_domain_features": [
            "dominant_frequency_hz",
            "spectral_centroid_hz",
            "spectral_energy",
            "spectral_entropy",
        ],
        "split": {"group": "measurement_id"},
    }
