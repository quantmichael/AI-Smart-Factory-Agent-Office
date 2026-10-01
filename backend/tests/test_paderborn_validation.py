from pathlib import Path

from app.data.adapters.paderborn import PaderbornDatasetAdapter


def test_validation_reports_fixture_statistics(paderborn_fixture: Path) -> None:
    result = PaderbornDatasetAdapter(paderborn_fixture).validate()

    assert result.status == "pass"
    assert result.measurement_count == 2
    assert result.bearing_count == 2
    assert result.healthy_count == 1
    assert result.damaged_count == 1
    assert result.unknown_count == 0
    assert result.invalid_measurement_count == 0
    assert result.signal_channel_distribution["vibration_1"] == 2
