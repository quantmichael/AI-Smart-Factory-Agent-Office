"""Health endpoint tests."""

import json
import re

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ai-smart-factory-agent-office-api",
        "version": "0.1.0",
    }


def test_openapi_exposes_health_endpoint() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/health" in response.json()["paths"]


def test_readiness_endpoint_does_not_expose_internal_paths() -> None:
    response = client.get("/api/v1/ready")

    assert response.status_code in {200, 503}
    serialized = json.dumps(response.json())
    assert "/Users/" not in serialized
    assert "/home/" not in serialized
    assert "/private/" not in serialized
    assert re.search(r"[A-Za-z]:\\\\Users\\\\", serialized) is None


@pytest.mark.parametrize("origin", ["http://localhost:3000", "http://127.0.0.1:3000"])
def test_frontend_origin_is_allowed_by_cors(origin: str) -> None:
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
