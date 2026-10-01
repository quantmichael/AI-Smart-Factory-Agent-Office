from fastapi.testclient import TestClient

from app.agent.schemas import AgentRunCreate
from app.api.v1.agent import get_agent_run_manager
from app.main import app
from api_helpers import build_fake_run_manager
from agent_helpers import ShutdownReviewPlanner


def test_report_is_available_only_after_completion(tmp_path):
    manager = build_fake_run_manager(tmp_path, planner=ShutdownReviewPlanner())
    created = manager.create_run(
        AgentRunCreate(equipment_id="fake-rig", measurement_id="fake:measurement:1")
    )
    manager.wait_for_status(created.run_id, {"WAITING"})
    app.dependency_overrides[get_agent_run_manager] = lambda: manager
    client = TestClient(app)
    try:
        not_ready = client.get(f"/api/v1/agent/runs/{created.run_id}/report")
        waiting = manager.get_run(created.run_id)
        accepted = client.post(
            f"/api/v1/agent/runs/{created.run_id}/human-input",
            json={
                "request_id": waiting.pending_human_request.request_id,
                "response": {"decision": "APPROVED"},
            },
        )
        manager.wait_for_status(created.run_id, {"COMPLETED"})
        report = client.get(f"/api/v1/agent/runs/{created.run_id}/report")
        duplicate = client.post(
            f"/api/v1/agent/runs/{created.run_id}/human-input",
            json={
                "request_id": waiting.pending_human_request.request_id,
                "response": {"decision": "APPROVED"},
            },
        )
    finally:
        app.dependency_overrides.clear()
        manager.close()

    assert not_ready.status_code == 409
    assert not_ready.json()["error"]["code"] == "REPORT_NOT_READY"
    assert accepted.status_code == 202
    assert report.status_code == 200
    assert report.json()["run_id"] == created.run_id
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "HUMAN_REQUEST_ALREADY_RESOLVED"
