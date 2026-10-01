"""Structured diagnosis and evidence-verification contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator, model_validator

from app.domain.schemas.common import StrictSchema
from app.domain.schemas import AgentEvent, WorkflowStatus


class EvidenceStatus(StrEnum):
    SUFFICIENT = "SUFFICIENT"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICTING = "CONFLICTING"


class ActionType(StrEnum):
    MONITOR = "MONITOR"
    INSPECT = "INSPECT"
    SCHEDULE_MAINTENANCE = "SCHEDULE_MAINTENANCE"
    EXPERT_REVIEW = "EXPERT_REVIEW"
    SHUTDOWN_CHECK = "SHUTDOWN_CHECK"


class ActionPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class HumanRequestType(StrEnum):
    ADDITIONAL_INFORMATION = "ADDITIONAL_INFORMATION"
    APPROVAL = "APPROVAL"


class ApprovalDecision(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVISION = "NEEDS_REVISION"


class DemoScenario(StrEnum):
    """Explicit, disclosed demo-only routing conditions."""

    HITL_CONTROLLED = "HITL_CONTROLLED"


class DiagnosisConfidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DiagnosisCandidate(StrictSchema):
    candidate_id: str = Field(min_length=1)
    fault_type: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    supporting_visual_observation_ids: list[str] = Field(default_factory=list)
    supporting_memory_ids: list[str] = Field(default_factory=list)
    confidence_level: DiagnosisConfidence
    uncertainties: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def references_do_not_overlap(self):
        if set(self.supporting_evidence_ids) & set(self.contradicting_evidence_ids):
            raise ValueError("an evidence ID cannot both support and contradict a candidate")
        return self


class VerificationResult(StrictSchema):
    status: EvidenceStatus
    supported_candidate_ids: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1)


class InspectionStep(StrictSchema):
    step_id: str = Field(min_length=1)
    order: int = Field(ge=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    related_candidate_ids: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    required_input: list[str] = Field(default_factory=list)
    safety_note: str | None = None


class RecommendedAction(StrictSchema):
    action_id: str = Field(min_length=1)
    action_type: ActionType
    priority: ActionPriority
    summary: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    requires_human_approval: bool = False
    limitations: list[str] = Field(default_factory=list)


class HumanRequest(StrictSchema):
    request_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    request_type: HumanRequestType
    question: str = Field(min_length=1)
    requested_fields: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=1)
    related_candidate_ids: list[str] = Field(default_factory=list)
    action_id: str | None = None
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def created_at_is_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value


class HumanInputSubmission(StrictSchema):
    request_id: str = Field(min_length=1)
    response: dict[str, Any]
    comment: str | None = Field(default=None, max_length=2000)
    actor: str | None = Field(default=None, min_length=1, max_length=200)


class HumanInteraction(StrictSchema):
    request_id: str
    request_type: HumanRequestType
    request: dict[str, Any]
    response: dict[str, Any]
    comment: str | None = None
    actor: str | None = None
    recorded_at: datetime

    @field_validator("recorded_at")
    @classmethod
    def recorded_at_is_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("recorded_at must be timezone-aware")
        return value


class ReportCitation(StrictSchema):
    evidence_id: str
    document_id: str
    chunk_id: str
    title: str
    publisher: str
    page: int | None = Field(default=None, ge=1)
    section: str | None = None
    official_url: str


class VersionTrace(StrictSchema):
    application_version: str
    model_id: str
    model_version: str
    knowledge_pack_id: str
    knowledge_manifest_version: str
    workflow_version: str


class FinalReport(StrictSchema):
    run_id: str
    equipment_id: str
    measurement_id: str
    demo_scenario: DemoScenario | None = None
    analysis_summary: dict[str, Any]
    diagnosis_candidates: list[DiagnosisCandidate]
    evidence_status: EvidenceStatus | None = None
    inspection_plan: list[InspectionStep]
    recommended_actions: list[RecommendedAction]
    human_interactions: list[HumanInteraction]
    limitations: list[str]
    citations: list[ReportCitation]
    historical_context_used: list[str] = Field(default_factory=list)
    visual_observations: list[dict[str, Any]] = Field(default_factory=list)
    visual_context_used: list[str] = Field(default_factory=list)
    version_trace: VersionTrace
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def created_at_is_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value


class HumanInputResult(StrictSchema):
    run_id: str
    workflow_status: str
    current_node: str
    next_action: str | None = None
    pending_human_request: HumanRequest | None = None
    final_report: FinalReport | dict[str, Any] | None = None


class AgentRunCreate(StrictSchema):
    equipment_id: str = Field(min_length=1)
    measurement_id: str = Field(min_length=1)
    inspection_image_ids: list[str] = Field(default_factory=list, max_length=3)
    demo_scenario: DemoScenario | None = None


class AgentRunCreated(StrictSchema):
    run_id: str
    status: WorkflowStatus
    current_node: str
    created_at: datetime


class AgentRunView(StrictSchema):
    run_id: str
    equipment_id: str
    measurement_id: str
    demo_scenario: DemoScenario | None = None
    workflow_status: WorkflowStatus
    current_node: str
    analysis_result: dict[str, Any] | None = None
    evidence_status: EvidenceStatus | None = None
    evidence_count: int = Field(default=0, ge=0)
    retrieval_retry_count: int = Field(default=0, ge=0)
    diagnosis_candidates: list[DiagnosisCandidate] = Field(default_factory=list)
    inspection_plan: list[InspectionStep] = Field(default_factory=list)
    recommended_actions: list[RecommendedAction] = Field(default_factory=list)
    memory_used_ids: list[str] = Field(default_factory=list)
    inspection_image_ids: list[str] = Field(default_factory=list)
    visual_observations: list[dict[str, Any]] = Field(default_factory=list)
    version_trace: VersionTrace
    pending_human_request: HumanRequest | None = None
    final_report_available: bool = False
    created_at: datetime
    updated_at: datetime


class AgentRunSummary(StrictSchema):
    run_id: str
    equipment_id: str
    measurement_id: str
    demo_scenario: DemoScenario | None = None
    workflow_status: WorkflowStatus
    ml_prediction: str | None = None
    ml_confidence: float | None = Field(default=None, ge=0, le=1)
    evidence_count: int = Field(default=0, ge=0)
    final_report_available: bool = False
    hitl_status: str = "NONE"
    created_at: datetime
    updated_at: datetime


class AgentRunList(StrictSchema):
    items: list[AgentRunSummary]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class AgentEventList(StrictSchema):
    run_id: str
    events: list[AgentEvent]


def validate_evidence_references(
    candidates: list[DiagnosisCandidate], evidence_ids: set[str]
) -> None:
    for candidate in candidates:
        referenced = set(candidate.supporting_evidence_ids) | set(
            candidate.contradicting_evidence_ids
        )
        unknown = referenced - evidence_ids
        if unknown:
            raise ValueError(
                f"diagnosis candidate {candidate.candidate_id} references unknown evidence IDs: "
                f"{sorted(unknown)}"
            )


def validate_plan_references(
    steps: list[InspectionStep],
    candidate_ids: set[str],
    evidence_ids: set[str],
) -> None:
    for step in steps:
        unknown_candidates = set(step.related_candidate_ids) - candidate_ids
        unknown_evidence = set(step.supporting_evidence_ids) - evidence_ids
        if unknown_candidates or unknown_evidence:
            raise ValueError(
                f"inspection step {step.step_id} has unsupported references: "
                f"candidates={sorted(unknown_candidates)}, evidence={sorted(unknown_evidence)}"
            )
