import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.v1.models import get_model_catalog_service
from app.core.config import get_settings, resolve_runtime_path
from app.main import app
from app.ml.catalog import ModelCatalogService


def test_current_model_matches_real_artifacts_without_exposing_internal_paths():
    response = TestClient(app).get("/api/v1/models/current")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "READY"
    assert body["model"]["model_id"] == "bearing_rf_binary_v1"
    assert body["model"]["model_type"] == "RandomForestClassifier"
    assert body["model"]["feature_count"] == 36
    assert len(body["features"]) == 36
    assert body["training_data"]["train_measurement_count"] == 180
    assert body["training_data"]["test_measurement_count"] == 60
    assert body["evaluation"]["levels"]["measurement_level"]["confusion_matrix"] == [
        [20, 0],
        [0, 40],
    ]
    assert body["feature_importance"][0]["feature"] == "phase_current_1__mean"
    serialized = response.text
    assert "model.joblib" not in serialized
    assert str(resolve_runtime_path(get_settings().ml_artifact_root)) not in serialized


def _minimal_artifact(root: Path, *, include_importance: bool = True) -> None:
    directory = root / "fixture_v1"
    directory.mkdir(parents=True)
    (directory / "model.joblib").write_bytes(b"not-loaded-by-catalog")
    (directory / "metadata.json").write_text(
        json.dumps(
            {
                "model_id": "fixture_model",
                "model_type": "RandomForestClassifier",
                "version": "1.0",
                "trained_at": "2026-01-01T00:00:00+00:00",
                "dataset": "fixture subset",
                "feature_version": "v1",
                "class_mapping": {"healthy": "normal", "damaged": "abnormal"},
                "feature_list": ["vibration_1__rms"],
            }
        ),
        encoding="utf-8",
    )
    if include_importance:
        (directory / "feature_importance.csv").write_text(
            "rank,feature,importance\n1,vibration_1__rms,1.0\n",
            encoding="utf-8",
        )


def test_optional_artifacts_can_be_missing_without_breaking_the_summary(tmp_path: Path):
    _minimal_artifact(tmp_path, include_importance=False)
    result = ModelCatalogService(tmp_path, "fixture_model").current()

    assert result.model.feature_count == 1
    assert result.feature_importance == []
    assert result.evaluation.levels == {}
    assert result.training_data.train_measurement_count is None


def test_missing_active_model_returns_public_not_found_error(tmp_path: Path):
    app.dependency_overrides[get_model_catalog_service] = lambda: ModelCatalogService(
        tmp_path,
        "missing_model",
    )
    try:
        response = TestClient(app).get("/api/v1/models/current")
    finally:
        app.dependency_overrides.pop(get_model_catalog_service, None)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MODEL_ARTIFACT_NOT_FOUND"


def test_invalid_model_metadata_returns_public_error(tmp_path: Path):
    directory = tmp_path / "broken"
    directory.mkdir()
    (directory / "model.joblib").write_bytes(b"not-loaded")
    (directory / "metadata.json").write_text("{broken", encoding="utf-8")
    app.dependency_overrides[get_model_catalog_service] = lambda: ModelCatalogService(
        tmp_path,
        "broken_model",
    )
    try:
        response = TestClient(app).get("/api/v1/models/current")
    finally:
        app.dependency_overrides.pop(get_model_catalog_service, None)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "MODEL_ARTIFACT_INVALID"
