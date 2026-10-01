from fastapi.testclient import TestClient

from app.api.v1.analysis import get_analysis_service
from app.domain.schemas import AnalysisResult
from app.main import app


class StubAnalysisService:
    def __init__(self) -> None:
        self.calls = []

    def analyze(self, measurement_id: str, model_id: str | None = None) -> AnalysisResult:
        self.calls.append((measurement_id, model_id))
        return AnalysisResult(
            analysis_id="analysis-test",
            measurement_id=measurement_id,
            model_id=model_id or "bearing_rf_binary_v1",
            status="normal",
            predicted_class="healthy",
            confidence=0.8,
            signal_features={"rms": 0.4},
            metadata={"feature_version": "step03_v1"},
        )


def test_analysis_api_returns_shared_contract() -> None:
    service = StubAnalysisService()
    app.dependency_overrides[get_analysis_service] = lambda: service
    try:
        response = TestClient(app).post(
            "/api/v1/analysis",
            json={"measurement_id": "measurement-1"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_id"] == "analysis-test"
    assert body["measurement_id"] == "measurement-1"
    assert body["model_id"] == "bearing_rf_binary_v1"
    assert body["status"] == "normal"
    assert service.calls == [("measurement-1", None)]


def test_analysis_api_accepts_explicit_model() -> None:
    service = StubAnalysisService()
    app.dependency_overrides[get_analysis_service] = lambda: service
    try:
        response = TestClient(app).post(
            "/api/v1/analysis",
            json={"measurement_id": "measurement-1", "model_id": "model-2"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["model_id"] == "model-2"
    assert service.calls == [("measurement-1", "model-2")]


def test_analysis_openapi_exposes_contracts() -> None:
    schema = TestClient(app).get("/openapi.json").json()

    assert "/api/v1/analysis" in schema["paths"]
    assert "AnalysisRequest" in schema["components"]["schemas"]
    assert "AnalysisResult" in schema["components"]["schemas"]
    assert "ErrorResponse" in schema["components"]["schemas"]
