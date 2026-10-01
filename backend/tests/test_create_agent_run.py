from fastapi.testclient import TestClient

from app.agent.schemas import AgentRunCreate
from app.api.v1.agent import get_agent_run_manager
from app.main import app
from api_helpers import build_fake_run_manager


def test_create_returns_before_background_work_completes_and_get_recovers_state(tmp_path):
    manager = build_fake_run_manager(tmp_path, status="normal")
    app.dependency_overrides[get_agent_run_manager] = lambda: manager
    client = TestClient(app)
    try:
        response = client.post(
            "/api/v1/agent/runs",
            json={"equipment_id": "fake-rig", "measurement_id": "fake:measurement:1"},
        )
        assert response.status_code == 202
        assert response.json()["status"] == "RUNNING"
        run_id = response.json()["run_id"]
        completed = manager.wait_for_status(run_id, {"COMPLETED"})
        recovered = client.get(f"/api/v1/agent/runs/{run_id}")
    finally:
        app.dependency_overrides.clear()
        manager.close()

    assert completed.current_node == "generate_normal_report"
    assert recovered.status_code == 200
    assert recovered.json()["final_report_available"] is True


def test_unknown_run_uses_common_error_schema(tmp_path):
    manager = build_fake_run_manager(tmp_path)
    app.dependency_overrides[get_agent_run_manager] = lambda: manager
    try:
        response = TestClient(app).get("/api/v1/agent/runs/missing")
    finally:
        app.dependency_overrides.clear()
        manager.close()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RUN_NOT_FOUND"


def test_completed_run_and_events_recover_after_manager_restart(tmp_path):
    first = build_fake_run_manager(tmp_path, status="normal")
    created = first.create_run(
        AgentRunCreate(equipment_id="fake-rig", measurement_id="fake:measurement:1")
    )
    first.wait_for_status(created.run_id, {"COMPLETED"})
    expected_count = len(first.get_events(created.run_id))
    first.close()

    recovered = build_fake_run_manager(tmp_path, status="normal")
    try:
        run = recovered.get_run(created.run_id)
        events = recovered.get_events(created.run_id)
    finally:
        recovered.close()

    assert run.workflow_status == "COMPLETED"
    assert len(events) == expected_count
