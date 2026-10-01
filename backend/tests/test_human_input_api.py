from pathlib import Path

from fastapi.testclient import TestClient

from app.agent.schemas import AgentRunCreate, DemoScenario, HumanInputSubmission
from app.agent.run_manager import AgentRunManager
from app.api.v1.agent import get_agent_run_manager
from app.main import app
from agent_helpers import ShutdownReviewPlanner, build_fake_agent_service


def test_human_input_endpoint_resumes_the_checkpointed_run(tmp_path: Path) -> None:
    service, _, _ = build_fake_agent_service(
        tmp_path / "checkpoint.sqlite3", planner=ShutdownReviewPlanner()
    )
    manager = AgentRunManager(service, tmp_path / "runs.sqlite3")
    created = manager.create_run(
        AgentRunCreate(equipment_id="fake-rig", measurement_id="fake:measurement:1")
    )
    waiting = manager.wait_for_status(created.run_id, {"WAITING"})
    app.dependency_overrides[get_agent_run_manager] = lambda: manager
    try:
        response = TestClient(app).post(
            f"/api/v1/agent/runs/{created.run_id}/human-input",
            json={
                "request_id": waiting.pending_human_request.request_id,
                "response": {"decision": "APPROVED"},
                "comment": "Reviewed.",
            },
        )
        completed = manager.wait_for_status(created.run_id, {"COMPLETED"})
    finally:
        app.dependency_overrides.clear()
        manager.close()

    assert response.status_code == 202
    body = response.json()
    assert body["run_id"] == created.run_id
    assert completed.workflow_status == "COMPLETED"


def test_controlled_hitl_demo_uses_real_workflow_and_waits_for_approval(tmp_path: Path) -> None:
    service, _, _ = build_fake_agent_service(tmp_path / "checkpoint.sqlite3")
    manager = AgentRunManager(service, tmp_path / "runs.sqlite3")
    created = manager.create_run(
        AgentRunCreate(
            equipment_id="fake-rig",
            measurement_id="fake:measurement:1",
            demo_scenario=DemoScenario.HITL_CONTROLLED,
        )
    )
    waiting = manager.wait_for_status(created.run_id, {"WAITING"})
    try:
        assert waiting.demo_scenario == DemoScenario.HITL_CONTROLLED
        assert waiting.pending_human_request.request_type == "APPROVAL"
        action = waiting.recommended_actions[0]
        assert action.action_type == "SHUTDOWN_CHECK"
        assert action.requires_human_approval is True

        manager.submit_human_input(
            created.run_id,
            HumanInputSubmission(
                request_id=waiting.pending_human_request.request_id,
                response={"decision": "APPROVED"},
                comment="Controlled demo approval.",
                actor="test-operator",
            ),
        )
        completed = manager.wait_for_status(created.run_id, {"COMPLETED"})
        assert completed.workflow_status == "COMPLETED"
    finally:
        manager.close()
