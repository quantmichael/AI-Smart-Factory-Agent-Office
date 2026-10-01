from pathlib import Path

from agent_helpers import build_fake_agent_service


def test_completed_workflow_contains_no_control_command_or_fake_approval(tmp_path: Path) -> None:
    service, _, _ = build_fake_agent_service(tmp_path / "checkpoint.sqlite3")
    try:
        state = service.start_run("fake:measurement:1", run_id="guardrail-run")
    finally:
        service.close()

    serialized = str(state["final_report"]).lower()
    assert "plc" not in serialized
    assert "bypass interlock" not in serialized
    assert "automatically shut down" not in serialized
    assert state["human_interactions"] == []
    assert state["recommended_actions"][0]["action_type"] == "INSPECT"
