from pathlib import Path

from agent_helpers import build_fake_agent_service


def test_abnormal_graph_retrieves_purpose_separated_evidence(tmp_path: Path) -> None:
    service, _, retriever = build_fake_agent_service(tmp_path / "checkpoint.sqlite3")
    try:
        state = service.start_run("fake:measurement:1", run_id="abnormal-run")
    finally:
        service.close()

    assert retriever.calls == 2
    assert {item["purpose"] for item in state["rag_evidence"]} == {
        "DIAGNOSTIC_EVIDENCE",
        "INSPECTION_ACTION",
    }
    assert state["evidence_status"] == "SUFFICIENT"
    assert state["next_action"] == "REPORT_COMPLETE"
    assert state["inspection_plan"]
    assert state["recommended_actions"]
    assert state["final_report"]["citations"]
