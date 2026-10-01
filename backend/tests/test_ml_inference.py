import joblib
import pytest

from app.ml.dataset import build_feature_table
from app.ml.inference import MLInferenceService, ModelNotFoundError
from app.ml.training.baseline import MODEL_ID, train_random_forest
from app.ml.training.split import stratified_measurement_split


def test_ml_inference_returns_analysis_result(
    tmp_path, ml_adapter, ml_input_spec
) -> None:
    table = build_feature_table(ml_adapter, ml_input_spec)
    split = stratified_measurement_split(table.records, test_size=0.5, random_state=42)
    model = train_random_forest(table, split)
    path = tmp_path / "model.joblib"
    joblib.dump(
        {
            "model": model,
            "model_id": MODEL_ID,
            "feature_names": list(table.feature_names),
            "classes": list(model.classes_),
        },
        path,
    )

    measurement_id = ml_adapter.list_measurements()[0].measurement_id
    result = MLInferenceService(ml_adapter, path, ml_input_spec).analyze(measurement_id)

    assert result.measurement_id == measurement_id
    assert result.model_id == MODEL_ID
    assert result.predicted_class in {"healthy", "damaged"}
    assert 0.5 <= result.confidence <= 1.0
    assert set(result.signal_features) == {
        "rms",
        "kurtosis",
        "crest_factor",
        "dominant_frequency_hz",
    }


def test_ml_inference_fails_when_model_is_missing(ml_adapter, ml_input_spec, tmp_path) -> None:
    with pytest.raises(ModelNotFoundError):
        MLInferenceService(ml_adapter, tmp_path / "missing.joblib", ml_input_spec)
