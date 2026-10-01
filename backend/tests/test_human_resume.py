from pathlib import Path

import pytest

from app.agent.schemas import EvidenceStatus, HumanInputSubmission
from agent_helpers import (
    InsufficientThenDeterministicVerifier,
    ShutdownReviewPlanner,
    build_fake_agent_service,
)
from test_verification_routing import FixedVerifier


@pytest.mark.parametrize("decision", ["APPROVED", "REJECTED"])
def test_approval_decision_resumes_same_run_and_is_audited(
    tmp_path: Path, decision: str
) -> None:
    service, analysis, _ = build_fake_agent_service(
        tmp_path / "checkpoint.sqlite3", planner=ShutdownReviewPlanner()
    )
    waiting = service.start_run("fake:measurement:1", run_id=f"approval-{decision}")
    submission = HumanInputSubmission(
        request_id=waiting["pending_human_request"]["request_id"],
        response={"decision": decision},
        comment="Reviewed by an authenticated layer outside this MVP.",
    )
    completed = service.submit_human_input(waiting["run_id"], submission)
    service.close()

    assert completed["run_id"] == waiting["run_id"]
    assert completed["workflow_status"] == "COMPLETED"
    assert completed["human_interactions"][-1]["response"]["decision"] == decision
    assert analysis.calls == 1
    if decision == "REJECTED":
        assert any("rejected" in item.lower() for item in completed["final_report"]["limitations"])


def test_additional_information_updates_human_context_and_retrieves_again(
    tmp_path: Path,
) -> None:
    verifier = InsufficientThenDeterministicVerifier()
    service, analysis, retriever = build_fake_agent_service(
        tmp_path / "checkpoint.sqlite3", verifier=verifier
    )
    waiting = service.start_run("fake:measurement:1", run_id="information-run")
    request = waiting["pending_human_request"]
    original_analysis = waiting["analysis_result"]
    completed = service.submit_human_input(
        waiting["run_id"],
        HumanInputSubmission(
            request_id=request["request_id"],
            response={
                "inspection_observation": "No visible leakage; abnormal noise was observed.",
                "operating_condition_confirmation": "N15_M07_F10 confirmed.",
            },
        ),
    )
    service.close()

    assert completed["workflow_status"] == "COMPLETED"
    assert completed["analysis_result"] == original_analysis
    assert completed["human_information_round_count"] == 1
    assert completed["human_observations"]
    assert all(item["source"] == "human" for item in completed["human_observations"])
    assert analysis.calls == 1
    assert retriever.calls > 2


def test_additional_information_requires_every_requested_field(tmp_path: Path) -> None:
    service, _, _ = build_fake_agent_service(
        tmp_path / "checkpoint.sqlite3",
        verifier=InsufficientThenDeterministicVerifier(),
    )
    waiting = service.start_run("fake:measurement:1", run_id="invalid-info-run")
    with pytest.raises(ValueError, match="missing requested fields"):
        service.submit_human_input(
            waiting["run_id"],
            HumanInputSubmission(
                request_id=waiting["pending_human_request"]["request_id"],
                response={"inspection_observation": "Observation only."},
            ),
        )
    still_waiting = service.get_run(waiting["run_id"])
    service.close()
    assert still_waiting["workflow_status"] == "WAITING"


def test_human_information_round_limit_produces_limited_report(tmp_path: Path) -> None:
    service, _, _ = build_fake_agent_service(
        tmp_path / "checkpoint.sqlite3",
        verifier=FixedVerifier(EvidenceStatus.INSUFFICIENT),
        max_human_rounds=1,
    )
    waiting = service.start_run("fake:measurement:1", run_id="bounded-human-run")
    request = waiting["pending_human_request"]
    completed = service.submit_human_input(
        waiting["run_id"],
        HumanInputSubmission(
            request_id=request["request_id"],
            response={field: "provided" for field in request["requested_fields"]},
        ),
    )
    service.close()

    assert completed["workflow_status"] == "COMPLETED"
    assert completed["evidence_status"] == "INSUFFICIENT"
    assert completed["human_information_round_count"] == 1
    assert any(
        "incomplete" in item.lower() for item in completed["final_report"]["limitations"]
    )
