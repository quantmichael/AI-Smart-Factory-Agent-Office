from app.ml.dataset import build_feature_table
from app.ml.training.baseline import train_random_forest
from app.ml.training.split import stratified_measurement_split


def test_ml_training_returns_binary_probability_model(ml_adapter, ml_input_spec) -> None:
    table = build_feature_table(ml_adapter, ml_input_spec)
    split = stratified_measurement_split(table.records, test_size=0.5, random_state=42)
    model = train_random_forest(table, split)

    probabilities = model.predict_proba(table.matrix(split.test))
    assert probabilities.shape == (len(split.test), 2)
    assert set(model.classes_) == {"healthy", "damaged"}
