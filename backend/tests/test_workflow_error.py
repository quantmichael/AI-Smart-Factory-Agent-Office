from pathlib import Path

from agent_helpers import build_fake_agent_service


def test_unrecoverable_data_error_is_not_disguised_as_normal(tmp_path: Path) -> None:
    service, analysis, retriever = build_fake_agent_service(tmp_path / "checkpoint.sqlite3")
    try:
        state = service.start_run("missing:measurement", run_id="failed-run")
    finally:
        service.close()

    assert state["workflow_status"] == "FAILED"
    assert state["errors"][0]["error_type"] == "DATA_ERROR"
    assert state["events"][-1]["event_type"] == "workflow_error"
    assert analysis.calls == 0
    assert retriever.calls == 0
