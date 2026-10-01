from pathlib import Path

from agent_helpers import ShutdownReviewPlanner, build_fake_agent_service


def test_no_human_answer_keeps_checkpointed_run_waiting(tmp_path: Path) -> None:
    service, analysis, retriever = build_fake_agent_service(
        tmp_path / "checkpoint.sqlite3", planner=ShutdownReviewPlanner()
    )
    state = service.start_run("fake:measurement:1", run_id="waiting-run")
    loaded = service.get_run("waiting-run")
    service.close()

    assert state["workflow_status"] == "WAITING"
    assert loaded["workflow_status"] == "WAITING"
    assert state["pending_human_request"]["request_type"] == "APPROVAL"
    assert state["next_action"] == "HUMAN_APPROVAL_REQUIRED"
    assert state["final_report"] is None
    assert analysis.calls == 1
    assert retriever.calls == 2
