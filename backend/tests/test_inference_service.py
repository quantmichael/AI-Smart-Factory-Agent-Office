from app.ml.inference import MLInferenceService


def test_inference_service_reuses_training_artifact_contract(
    tmp_path, ml_adapter, ml_input_spec
) -> None:
    from app.ml.dataset import build_feature_table
    from app.ml.training.baseline import train_random_forest
    from app.ml.training.split import stratified_measurement_split
    import joblib
    import json

    table = build_feature_table(ml_adapter, ml_input_spec)
    split = stratified_measurement_split(table.records, test_size=0.5, random_state=42)
    model = train_random_forest(table, split)
    bundle = {
        "model": model,
        "model_id": "fixture-model",
        "model_version": "1",
        "feature_version": "fixture-v1",
        "feature_names": list(table.feature_names),
        "classes": list(model.classes_),
    }
    joblib.dump(bundle, tmp_path / "model.joblib")
    (tmp_path / "input_spec.json").write_text(json.dumps(ml_input_spec), encoding="utf-8")
    (tmp_path / "metadata.json").write_text(
        json.dumps(
            {
                "model_id": "fixture-model",
                "feature_version": "fixture-v1",
                "feature_list": list(table.feature_names),
            }
        ),
        encoding="utf-8",
    )

    service = MLInferenceService.from_artifact(ml_adapter, tmp_path)
    result = service.analyze(ml_adapter.list_measurements()[0].measurement_id)

    assert result.metadata["model_version"] == "1"
    assert result.metadata["feature_version"] == "fixture-v1"
    assert result.metadata["timing_ms"]["measurement_load"] >= 0
    assert result.metadata["timing_ms"]["model_inference"] >= 0
    assert result.metadata["inference_timestamp"].endswith("+00:00")
