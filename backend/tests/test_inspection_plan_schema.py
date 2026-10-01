from pathlib import Path

import pytest

from app.agent.schemas import InspectionStep, validate_plan_references
from agent_helpers import build_fake_agent_service


def test_inspection_plan_links_existing_candidates_and_evidence(tmp_path: Path) -> None:
    service, _, _ = build_fake_agent_service(tmp_path / "checkpoint.sqlite3")
    try:
        state = service.start_run("fake:measurement:1", run_id="inspection-run")
    finally:
        service.close()

    candidate_ids = {item["candidate_id"] for item in state["diagnosis_candidates"]}
    evidence_ids = {item["evidence_id"] for item in state["rag_evidence"]}
    steps = [InspectionStep.model_validate(item) for item in state["inspection_plan"]]
    validate_plan_references(steps, candidate_ids, evidence_ids)
    assert [item.order for item in steps] == list(range(1, len(steps) + 1))
    assert all(item.supporting_evidence_ids for item in steps)


def test_inspection_plan_rejects_invented_references() -> None:
    step = InspectionStep(
        step_id="INS-001",
        order=1,
        title="Inspect",
        description="Inspect available context.",
        reason="Verification",
        related_candidate_ids=["invented-candidate"],
        supporting_evidence_ids=["invented-evidence"],
    )
    with pytest.raises(ValueError, match="unsupported references"):
        validate_plan_references([step], {"candidate-real"}, {"evidence-real"})
