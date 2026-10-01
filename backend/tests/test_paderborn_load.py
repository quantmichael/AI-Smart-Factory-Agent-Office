from pathlib import Path

import numpy as np
import pytest

from app.data.adapters.paderborn import PaderbornDatasetAdapter


def test_load_returns_observed_channels_and_sampling(paderborn_fixture: Path) -> None:
    adapter = PaderbornDatasetAdapter(paderborn_fixture)
    measurement = adapter.load_measurement("paderborn:K001:N15_M07_F10:01")

    assert set(measurement.signals) == {
        "force",
        "phase_current_1",
        "phase_current_2",
        "speed",
        "temp_2_bearing_module",
        "torque",
        "vibration_1",
    }
    vibration = measurement.signals["vibration_1"]
    assert vibration.sampling.nominal_rate_hz == 64_000
    assert vibration.values.size == vibration.time.size == 9
    assert np.isfinite(vibration.values).all()
    assert measurement.summary.ground_truth.state == "healthy"


@pytest.mark.integration
def test_real_dataset_loads_one_healthy_and_one_damaged_measurement() -> None:
    root = Path(__file__).resolve().parents[2] / "data/paderborn"
    if not any(root.rglob("*.mat")):
        pytest.skip("local Paderborn dataset is not available")
    adapter = PaderbornDatasetAdapter(root)
    by_state = {}
    for summary in adapter.list_measurements():
        by_state.setdefault(summary.ground_truth.state, summary.measurement_id)

    healthy = adapter.load_measurement(by_state["healthy"])
    damaged = adapter.load_measurement(by_state["damaged"])

    assert healthy.signals["vibration_1"].values.size > 0
    assert damaged.signals["phase_current_1"].values.size > 0
    assert np.isfinite(healthy.signals["vibration_1"].values).all()
    assert np.isfinite(damaged.signals["phase_current_1"].values).all()
