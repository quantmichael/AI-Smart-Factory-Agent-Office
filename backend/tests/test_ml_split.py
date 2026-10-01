from app.ml.dataset import build_feature_table
from app.ml.training.split import stratified_measurement_split


def test_ml_split_is_reproducible_and_has_no_measurement_leakage(
    ml_adapter, ml_input_spec
) -> None:
    table = build_feature_table(ml_adapter, ml_input_spec)
    first = stratified_measurement_split(table.records, test_size=0.5, random_state=42)
    second = stratified_measurement_split(table.records, test_size=0.5, random_state=42)

    assert first.train_measurements == second.train_measurements
    assert first.test_measurements == second.test_measurements
    assert set(first.train_measurements).isdisjoint(first.test_measurements)
    assert {row.measurement_id for row in first.train}.isdisjoint(
        row.measurement_id for row in first.test
    )
