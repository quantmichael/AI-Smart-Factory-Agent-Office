import pytest

from app.data.adapters.base import SensorDatasetAdapter


def test_sensor_dataset_adapter_is_abstract() -> None:
    with pytest.raises(TypeError):
        SensorDatasetAdapter()
