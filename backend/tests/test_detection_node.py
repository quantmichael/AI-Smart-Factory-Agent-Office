from pathlib import Path

from agent_helpers import build_fake_agent_service


def test_normal_graph_reuses_analysis_service_and_skips_rag(tmp_path: Path) -> None:
    service, analysis, retriever = build_fake_agent_service(
        tmp_path / "checkpoint.sqlite3", status="normal"
    )
    try:
        state = service.start_run("fake:measurement:1", run_id="normal-run")
    finally:
        service.close()

    assert analysis.calls == 1
    assert retriever.calls == 0
    assert state["workflow_status"] == "COMPLETED"
    assert state["final_report"]["analysis_summary"]["status"] == "normal"
    assert state["final_report"]["diagnosis_candidates"] == []
    assert state["rag_evidence"] == []
