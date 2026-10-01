import json

from app.ml.registry import ArtifactModelRegistry


def test_model_registry_resolves_configured_active_model(tmp_path) -> None:
    artifact = tmp_path / "baseline"
    artifact.mkdir()
    (artifact / "metadata.json").write_text(
        json.dumps(
            {
                "model_id": "active-model",
                "feature_version": "features-v1",
                "class_mapping": {"healthy": "normal", "damaged": "abnormal"},
            }
        ),
        encoding="utf-8",
    )
    (artifact / "model.joblib").write_bytes(b"model")

    entry = ArtifactModelRegistry(tmp_path, "active-model").get_active_model()

    assert entry.model_id == "active-model"
    assert entry.metadata["feature_version"] == "features-v1"
    assert entry.metadata["class_mapping"]["damaged"] == "abnormal"
