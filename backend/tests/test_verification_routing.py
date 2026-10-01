from pathlib import Path

from app.agent.schemas import EvidenceStatus, VerificationResult
from agent_helpers import build_fake_agent_service


class FixedVerifier:
    def __init__(self, status: EvidenceStatus) -> None:
        self.status = status

    def verify(self, candidates, evidence):
        return VerificationResult(
            status=self.status,
            supported_candidate_ids=[item.candidate_id for item in candidates],
            missing_information=["inspection evidence"] if self.status == "PARTIAL" else [],
            conflicts=["alternative contexts"] if self.status == "CONFLICTING" else [],
            summary=f"Controlled {self.status} result.",
        )


def test_insufficient_routes_to_waiting_without_inventing_diagnosis(tmp_path: Path) -> None:
    service, _, _ = build_fake_agent_service(
        tmp_path / "checkpoint.sqlite3",
        verifier=FixedVerifier(EvidenceStatus.INSUFFICIENT),
    )
    try:
        state = service.start_run("fake:measurement:1", run_id="insufficient-run")
    finally:
        service.close()

    assert state["workflow_status"] == "WAITING"
    assert state["next_action"] == "ADDITIONAL_INFORMATION_REQUIRED"
    assert state["retrieval_retry_count"] == 0


def test_conflicting_uses_counter_evidence_route_until_retry_limit(tmp_path: Path) -> None:
    service, _, retriever = build_fake_agent_service(
        tmp_path / "checkpoint.sqlite3",
        verifier=FixedVerifier(EvidenceStatus.CONFLICTING),
    )
    try:
        state = service.start_run("fake:measurement:1", run_id="conflicting-run")
    finally:
        service.close()

    nodes = [event["node"] for event in state["events"]]
    assert "retrieve_counter_evidence" in nodes
    assert state["retrieval_retry_count"] == 2
    assert state["workflow_status"] == "WAITING"
    assert retriever.calls == 4
