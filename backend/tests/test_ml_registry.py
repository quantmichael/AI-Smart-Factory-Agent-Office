import json

import pytest

from app.ml.inference import ModelNotFoundError
from app.ml.registry import ArtifactModelRegistry


def test_artifact_model_registry_discovers_metadata(tmp_path) -> None:
    artifact = tmp_path / "baseline_v1"
    artifact.mkdir()
    (artifact / "metadata.json").write_text(
        json.dumps({"model_id": "model-1", "version": "1"}),
        encoding="utf-8",
    )
    (artifact / "model.joblib").write_bytes(b"fixture")

    entry = ArtifactModelRegistry(tmp_path).get("model-1")

    assert entry.model_path == artifact / "model.joblib"
    assert entry.metadata["version"] == "1"


def test_artifact_model_registry_rejects_unknown_model(tmp_path) -> None:
    with pytest.raises(ModelNotFoundError):
        ArtifactModelRegistry(tmp_path).get("missing")
