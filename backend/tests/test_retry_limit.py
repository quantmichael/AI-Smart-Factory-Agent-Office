from pathlib import Path

from app.agent.schemas import EvidenceStatus
from agent_helpers import build_fake_agent_service
from test_verification_routing import FixedVerifier


def test_partial_refines_query_and_stops_at_configured_limit(tmp_path: Path) -> None:
    service, _, retriever = build_fake_agent_service(
        tmp_path / "checkpoint.sqlite3",
        verifier=FixedVerifier(EvidenceStatus.PARTIAL),
        max_retries=2,
    )
    try:
        state = service.start_run("fake:measurement:1", run_id="partial-run")
    finally:
        service.close()

    completed_nodes = [
        event["node"] for event in state["events"] if event["event_type"] == "node_completed"
    ]
    assert completed_nodes.count("refine_query") == 2
    assert state["retrieval_retry_count"] == 2
    assert state["workflow_status"] == "WAITING"
    assert retriever.calls == 4
