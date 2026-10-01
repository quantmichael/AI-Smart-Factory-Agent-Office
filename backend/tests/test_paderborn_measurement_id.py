from pathlib import Path

import pytest

from app.data.adapters.paderborn import PaderbornDatasetAdapter
from app.data.errors import MeasurementNotFoundError


def test_measurement_ids_are_stable_and_paths_are_not_accepted(
    paderborn_fixture: Path,
) -> None:
    first = PaderbornDatasetAdapter(paderborn_fixture)
    second = PaderbornDatasetAdapter(paderborn_fixture)

    assert [item.measurement_id for item in first.list_measurements()] == [
        item.measurement_id for item in second.list_measurements()
    ]
    assert first.list_measurements()[0].measurement_id == (
        "paderborn:K001:N15_M07_F10:01"
    )
    with pytest.raises(MeasurementNotFoundError):
        first.load_measurement("../../outside.mat")
