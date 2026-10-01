from pathlib import Path

from agent_helpers import build_fake_agent_service


def test_final_report_citations_come_only_from_retrieved_evidence(tmp_path: Path) -> None:
    service, _, _ = build_fake_agent_service(tmp_path / "checkpoint.sqlite3")
    try:
        state = service.start_run("fake:measurement:1", run_id="citation-run")
    finally:
        service.close()

    evidence = {item["evidence_id"]: item for item in state["rag_evidence"]}
    citations = state["final_report"]["citations"]
    assert citations
    for citation in citations:
        source = evidence[citation["evidence_id"]]
        assert citation["document_id"] == source["document_id"]
        assert citation["chunk_id"] == source["chunk_id"]
        assert citation["official_url"] == source["official_url"]
        assert citation["page"] == source["page"]
