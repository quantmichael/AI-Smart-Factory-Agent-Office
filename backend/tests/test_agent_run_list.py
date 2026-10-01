from fastapi.testclient import TestClient

from app.agent.schemas import AgentRunCreate
from app.api.v1.agent import get_agent_run_manager
from app.main import app
from api_helpers import build_fake_run_manager
from agent_helpers import ShutdownReviewPlanner


def test_run_list_is_paginated_latest_first_and_filterable(tmp_path):
    manager = build_fake_run_manager(tmp_path, status="normal")
    created = []
    for _ in range(3):
        run = manager.create_run(
            AgentRunCreate(equipment_id="fake-rig", measurement_id="fake:measurement:1")
        )
        manager.wait_for_status(run.run_id, {"COMPLETED"})
        created.append(run)

    app.dependency_overrides[get_agent_run_manager] = lambda: manager
    client = TestClient(app)
    try:
        first_page = client.get("/api/v1/agent/runs?page=1&page_size=2")
        filtered = client.get(
            "/api/v1/agent/runs",
            params={
                "workflow_status": "COMPLETED",
                "measurement_id": "measurement:1",
                "equipment_id": "FAKE-RIG",
                "ml_prediction": "normal",
            },
        )
        empty = client.get(
            "/api/v1/agent/runs", params={"measurement_id": "does-not-exist"}
        )
    finally:
        app.dependency_overrides.clear()
        manager.close()

    assert first_page.status_code == 200
    body = first_page.json()
    assert body["total"] == 3
    assert body["total_pages"] == 2
    assert len(body["items"]) == 2
    assert body["items"][0]["created_at"] >= body["items"][1]["created_at"]
    assert body["items"][0]["ml_prediction"] == "normal"
    assert body["items"][0]["ml_confidence"] is not None
    assert body["items"][0]["hitl_status"] == "NONE"

    assert filtered.status_code == 200
    assert filtered.json()["total"] == 3
    assert empty.status_code == 200
    assert empty.json()["items"] == []
    assert empty.json()["total_pages"] == 0


def test_run_list_rejects_invalid_filters(tmp_path):
    manager = build_fake_run_manager(tmp_path)
    app.dependency_overrides[get_agent_run_manager] = lambda: manager
    try:
        response = TestClient(app).get(
            "/api/v1/agent/runs", params={"ml_prediction": "invented", "page_size": 0}
        )
    finally:
        app.dependency_overrides.clear()
        manager.close()

    assert response.status_code == 422


def test_run_list_reports_persisted_hitl_state(tmp_path):
    manager = build_fake_run_manager(tmp_path, planner=ShutdownReviewPlanner())
    created = manager.create_run(
        AgentRunCreate(equipment_id="fake-rig", measurement_id="fake:measurement:1")
    )
    waiting = manager.wait_for_status(created.run_id, {"WAITING"})
    app.dependency_overrides[get_agent_run_manager] = lambda: manager
    client = TestClient(app)
    try:
        pending = client.get("/api/v1/agent/runs").json()["items"][0]
        accepted = client.post(
            f"/api/v1/agent/runs/{created.run_id}/human-input",
            json={
                "request_id": waiting.pending_human_request.request_id,
                "response": {"decision": "APPROVED"},
            },
        )
        manager.wait_for_status(created.run_id, {"COMPLETED"})
        resolved = client.get("/api/v1/agent/runs").json()["items"][0]
    finally:
        app.dependency_overrides.clear()
        manager.close()

    assert pending["hitl_status"] == "PENDING"
    assert accepted.status_code == 202
    assert resolved["hitl_status"] == "RESOLVED"
