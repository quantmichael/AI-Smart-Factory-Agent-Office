import numpy as np

from app.ml.dataset import build_feature_table


def test_ml_dataset_preserves_audit_columns_and_feature_order(ml_adapter, ml_input_spec) -> None:
    table = build_feature_table(ml_adapter, ml_input_spec)

    assert len(table.records) == 8
    assert len(table.feature_names) == 36
    assert table.matrix().shape == (8, 36)
    assert np.isfinite(table.matrix()).all()
    assert {record.measurement_id for record in table.records} == {
        item.measurement_id for item in ml_adapter.list_measurements()
    }
    assert all(record.window_end - record.window_start == 64 for record in table.records)
