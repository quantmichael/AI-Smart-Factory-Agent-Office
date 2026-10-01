"""Evidence-linked inspection and recommendation drafting boundary."""

from __future__ import annotations

import hashlib
from typing import Protocol

from app.agent.schemas import (
    ActionPriority,
    ActionType,
    DiagnosisCandidate,
    InspectionStep,
    RecommendedAction,
)
from app.domain.schemas import EvidenceObject


class ActionPlanner(Protocol):
    provider_id: str

    def build_inspection_plan(
        self,
        candidates: list[DiagnosisCandidate],
        evidence: list[EvidenceObject],
    ) -> list[InspectionStep]: ...

    def recommend_action(
        self,
        candidates: list[DiagnosisCandidate],
        evidence: list[EvidenceObject],
        plan: list[InspectionStep],
    ) -> list[RecommendedAction]: ...


class ConservativeActionPlanner:
    provider_id = "deterministic-evidence-linked-actions-v1"

    def build_inspection_plan(
        self,
        candidates: list[DiagnosisCandidate],
        evidence: list[EvidenceObject],
    ) -> list[InspectionStep]:
        if not candidates or not evidence:
            return []
        candidate_ids = [item.candidate_id for item in candidates]
        diagnostic = next(
            (item for item in evidence if item.purpose == "DIAGNOSTIC_EVIDENCE"), None
        )
        inspection = next(
            (item for item in evidence if item.purpose == "INSPECTION_ACTION"), None
        )
        steps: list[InspectionStep] = []
        if diagnostic:
            steps.append(
                InspectionStep(
                    step_id="INS-001",
                    order=1,
                    title="Confirm the recorded vibration condition",
                    description=(
                        "Review the measurement features and operating condition against the "
                        f"diagnostic context in {diagnostic.title}"
                        + (f", {diagnostic.section}." if diagnostic.section else ".")
                    ),
                    reason="Confirm that the anomaly remains relevant under the recorded condition.",
                    related_candidate_ids=candidate_ids,
                    supporting_evidence_ids=[diagnostic.evidence_id],
                    required_input=["operating_condition_confirmation", "vibration_observation"],
                    safety_note="Follow site procedures; this step does not command equipment operation.",
                )
            )
        if inspection:
            steps.append(
                InspectionStep(
                    step_id=f"INS-{len(steps) + 1:03d}",
                    order=len(steps) + 1,
                    title="Inspect accessible bearing-condition indicators",
                    description=(
                        "Record observable bearing, lubrication, temperature, noise, and maintenance "
                        f"context while consulting {inspection.title}"
                        + (f", {inspection.section}." if inspection.section else ".")
                    ),
                    reason="Physical observations are needed before assigning a specific root cause.",
                    related_candidate_ids=candidate_ids,
                    supporting_evidence_ids=[inspection.evidence_id],
                    required_input=["inspection_observation", "maintenance_history"],
                    safety_note="Do not bypass guards or perform work beyond authorized site procedures.",
                )
            )
        return steps

    def recommend_action(
        self,
        candidates: list[DiagnosisCandidate],
        evidence: list[EvidenceObject],
        plan: list[InspectionStep],
    ) -> list[RecommendedAction]:
        if not candidates or not plan:
            return []
        evidence_ids = list(
            dict.fromkeys(
                evidence_id for step in plan for evidence_id in step.supporting_evidence_ids
            )
        )
        identity = ":".join(evidence_ids)
        return [
            RecommendedAction(
                action_id="action_" + hashlib.sha256(identity.encode()).hexdigest()[:16],
                action_type=ActionType.INSPECT,
                priority=ActionPriority.MEDIUM,
                summary="Perform the evidence-linked inspection plan before maintenance decisions.",
                reason=(
                    "The ML anomaly and retrieved technical context support inspection, but not an "
                    "automatic shutdown or a confirmed root-cause finding."
                ),
                supporting_evidence_ids=evidence_ids,
                limitations=[
                    "Priority is an internal workflow priority, not a legal safety classification.",
                    "No maintenance action is automatically executed.",
                ],
            )
        ]
