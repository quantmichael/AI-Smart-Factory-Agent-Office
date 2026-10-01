import pytest
from pydantic import ValidationError

from app.agent.schemas import DiagnosisCandidate, validate_evidence_references


def test_diagnosis_candidate_rejects_invalid_structured_output() -> None:
    with pytest.raises(ValidationError):
        DiagnosisCandidate(
            candidate_id="candidate-1",
            fault_type="bearing_anomaly",
            summary="Candidate only.",
            confidence_level="certain",
        )
    with pytest.raises(ValidationError):
        DiagnosisCandidate(
            candidate_id="candidate-1",
            fault_type="bearing_anomaly",
            confidence_level="low",
        )


def test_diagnosis_candidate_rejects_unknown_or_overlapping_evidence_ids() -> None:
    with pytest.raises(ValidationError, match="both support and contradict"):
        DiagnosisCandidate(
            candidate_id="candidate-1",
            fault_type="bearing_anomaly",
            summary="Candidate only.",
            confidence_level="low",
            supporting_evidence_ids=["evidence-1"],
            contradicting_evidence_ids=["evidence-1"],
        )
    candidate = DiagnosisCandidate(
        candidate_id="candidate-1",
        fault_type="bearing_anomaly",
        summary="Candidate only.",
        confidence_level="low",
        supporting_evidence_ids=["invented-evidence"],
    )
    with pytest.raises(ValueError, match="unknown evidence IDs"):
        validate_evidence_references([candidate], {"real-evidence"})
