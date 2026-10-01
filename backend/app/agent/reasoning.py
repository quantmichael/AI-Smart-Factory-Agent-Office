"""Pluggable structured reasoning boundary with a conservative local baseline."""

from __future__ import annotations

import hashlib
from typing import Any, Protocol

from app.agent.schemas import (
    DiagnosisCandidate,
    DiagnosisConfidence,
    EvidenceStatus,
    VerificationResult,
    validate_evidence_references,
)
from app.domain.schemas import AnalysisResult, EvidenceObject


class DiagnosisReasoner(Protocol):
    provider_id: str

    def diagnose(
        self,
        analysis: AnalysisResult,
        evidence: list[EvidenceObject],
        *,
        equipment_memory: dict[str, Any] | None = None,
        visual_observations: list[dict[str, Any]] | None = None,
    ) -> list[DiagnosisCandidate]: ...


class EvidenceVerifier(Protocol):
    def verify(
        self,
        candidates: list[DiagnosisCandidate],
        evidence: list[EvidenceObject],
    ) -> VerificationResult: ...


class ConservativeEvidenceReasoner:
    """Create no specific failure claim beyond the ML result and retrieved evidence."""

    provider_id = "deterministic-evidence-grounded-v1"

    def diagnose(
        self,
        analysis: AnalysisResult,
        evidence: list[EvidenceObject],
        *,
        equipment_memory: dict[str, Any] | None = None,
        visual_observations: list[dict[str, Any]] | None = None,
    ) -> list[DiagnosisCandidate]:
        if not evidence:
            return []
        supporting = [item.evidence_id for item in evidence[:8]]
        identity = f"{analysis.analysis_id}:{':'.join(supporting)}"
        uncertainties = [
            "The ML confidence is not a calibrated equipment-failure probability.",
            "A specific physical failure mechanism requires inspection evidence.",
        ]
        memory_count = len((equipment_memory or {}).get("memory_used_ids", []))
        memory_ids = list((equipment_memory or {}).get("memory_used_ids", []))
        if memory_count:
            uncertainties.append(
                f"{memory_count} prior equipment-memory record(s) were considered as history, "
                "not as technical evidence or confirmed root-cause facts."
            )
        visual_ids = [
            item["observation_id"]
            for result in (visual_observations or [])
            if result.get("quality") == "USABLE"
            for item in result.get("observations", [])
            if item.get("category") != "image_quality"
        ]
        if visual_observations:
            uncertainties.append(
                "Visual observations describe only directly visible exterior conditions and do not establish an internal bearing fault."
            )
        return [
            DiagnosisCandidate(
                candidate_id="candidate_" + hashlib.sha256(identity.encode()).hexdigest()[:16],
                fault_type="bearing_condition_anomaly",
                summary=(
                    f"The ML result classified the measurement as {analysis.predicted_class}. "
                    "Retrieved technical documents provide related diagnostic and inspection "
                    "context, but do not by themselves establish a specific physical root cause."
                ),
                supporting_evidence_ids=supporting,
                supporting_visual_observation_ids=visual_ids,
                supporting_memory_ids=memory_ids,
                confidence_level=DiagnosisConfidence.LOW,
                uncertainties=uncertainties,
            )
        ]


class DeterministicEvidenceVerifier:
    def verify(
        self,
        candidates: list[DiagnosisCandidate],
        evidence: list[EvidenceObject],
    ) -> VerificationResult:
        evidence_ids = {item.evidence_id for item in evidence}
        validate_evidence_references(candidates, evidence_ids)
        if not candidates or not evidence:
            return VerificationResult(
                status=EvidenceStatus.INSUFFICIENT,
                missing_information=["diagnostic and inspection technical evidence"],
                summary="No evidence-grounded diagnosis candidate can be formed.",
            )
        if any(candidate.contradicting_evidence_ids for candidate in candidates):
            return VerificationResult(
                status=EvidenceStatus.CONFLICTING,
                supported_candidate_ids=[item.candidate_id for item in candidates],
                conflicts=["The candidate contains explicitly contradicting evidence references."],
                summary="Retrieved evidence contains an unresolved conflict.",
            )
        purposes = {item.purpose for item in evidence}
        missing = []
        if "DIAGNOSTIC_EVIDENCE" not in purposes:
            missing.append("diagnostic evidence")
        if "INSPECTION_ACTION" not in purposes:
            missing.append("inspection evidence")
        if missing:
            return VerificationResult(
                status=EvidenceStatus.PARTIAL,
                supported_candidate_ids=[item.candidate_id for item in candidates],
                missing_information=missing,
                summary="Relevant evidence exists, but purpose coverage is incomplete.",
            )
        return VerificationResult(
            status=EvidenceStatus.SUFFICIENT,
            supported_candidate_ids=[item.candidate_id for item in candidates],
            summary=(
                "Evidence is sufficient to proceed to inspection planning; this does not "
                "confirm a physical fault."
            ),
        )
