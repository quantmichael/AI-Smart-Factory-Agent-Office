"""Stable cross-module contracts introduced by STEP 01."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictSchema(BaseModel):
    """Base schema that rejects accidental contract drift."""

    model_config = ConfigDict(extra="forbid")


class AnalysisStatus(StrEnum):
    """Normalized ML analysis status."""

    NORMAL = "normal"
    ABNORMAL = "abnormal"


class WorkflowStatus(StrEnum):
    """Canonical top-level workflow statuses approved for the project."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MeasurementRef(StrictSchema):
    """Dataset-independent reference to a measurement."""

    measurement_id: str = Field(min_length=1)
    equipment_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(StrictSchema):
    """Normalized output shared by future condition models."""

    analysis_id: str = Field(min_length=1)
    measurement_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    status: AnalysisStatus
    predicted_class: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    anomaly_score: float | None = None
    signal_features: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceObject(StrictSchema):
    """Citation-ready technical evidence returned by future retrieval code."""

    evidence_id: str = Field(min_length=1)
    query_id: str | None = None
    purpose: str | None = None
    document_id: str = Field(min_length=1)
    chunk_id: str = Field(min_length=1)
    source_id: str | None = None
    title: str = Field(min_length=1)
    publisher: str = Field(min_length=1)
    document_type: str = Field(min_length=1)
    source_tier: int = Field(ge=1, le=4)
    page: int | None = Field(default=None, ge=1)
    section: str | None = None
    content: str = Field(min_length=1)
    retrieval_score: float | None = None
    official_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentEvent(StrictSchema):
    """Ordered backend event contract for the future SSE stream."""

    event_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    event_type: str = Field(min_length=1)
    node: str = Field(min_length=1)
    agent_role: str = Field(min_length=1)
    message: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        """Reject ambiguous timestamps without a UTC offset."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value
