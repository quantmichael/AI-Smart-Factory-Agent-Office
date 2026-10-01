import pytest
from fastapi.testclient import TestClient

from app.api.v1.analysis import get_analysis_service
from app.data.errors import MeasurementNotFoundError
from app.main import app
from app.ml.inference import InferenceError, InvalidFeatureError, ModelLoadError, ModelNotFoundError
from app.services.analysis import FeatureExtractionError


class RaisingService:
    def __init__(self, error: Exception):
        self.error = error

    def analyze(self, measurement_id: str, model_id: str | None = None):
        raise self.error


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (MeasurementNotFoundError("internal path"), 404, "MEASUREMENT_NOT_FOUND"),
        (ModelNotFoundError("internal path"), 404, "MODEL_NOT_FOUND"),
        (ModelLoadError("pickle details"), 500, "MODEL_LOAD_FAILED"),
        (InvalidFeatureError("feature names"), 500, "MODEL_FEATURE_MISMATCH"),
        (FeatureExtractionError("raw details"), 500, "FEATURE_EXTRACTION_FAILED"),
        (InferenceError("library details"), 500, "INFERENCE_FAILED"),
    ],
)
def test_analysis_errors_use_public_schema(error, status, code) -> None:
    app.dependency_overrides[get_analysis_service] = lambda: RaisingService(error)
    try:
        response = TestClient(app, raise_server_exceptions=False).post(
            "/api/v1/analysis", json={"measurement_id": "measurement-1"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert "internal path" not in response.text


@pytest.mark.parametrize("payload", [{}, {"measurement_id": ""}, {"measurement_id": "m", "extra": 1}])
def test_invalid_analysis_request_uses_error_schema(payload) -> None:
    response = TestClient(app).post("/api/v1/analysis", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
