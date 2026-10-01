"""Contracts for deterministic query construction and citation-ready retrieval."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from app.domain.schemas import EvidenceObject
from app.domain.schemas.common import StrictSchema


class RetrievalPurpose(StrEnum):
    DATASET_EVIDENCE = "DATASET_EVIDENCE"
    DIAGNOSTIC_EVIDENCE = "DIAGNOSTIC_EVIDENCE"
    INSPECTION_ACTION = "INSPECTION_ACTION"


class RetrievalMode(StrEnum):
    DIAGNOSTIC = "DIAGNOSTIC"
    EVALUATION = "EVALUATION"


class RetrievalContext(StrictSchema):
    analysis_id: str | None = None
    measurement_id: str | None = None
    equipment_type: str = "rotating_machinery"
    component: str = "bearing"
    status: str
    predicted_class: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    signal_features: dict[str, float] = Field(default_factory=dict)
    bearing_id: str | None = None
    operating_condition: str | None = None
    mode: RetrievalMode = RetrievalMode.DIAGNOSTIC


class RetrievalQuery(StrictSchema):
    query_id: str = Field(min_length=1)
    purpose: RetrievalPurpose
    mode: RetrievalMode = RetrievalMode.DIAGNOSTIC
    query_text: str = Field(min_length=1, max_length=4000)
    filters: dict[str, Any] = Field(default_factory=dict)
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievalStats(StrictSchema):
    returned: int = Field(ge=0)
    latency_ms: float = Field(ge=0)
    source_tiers: dict[str, int] = Field(default_factory=dict)
    document_types: dict[str, int] = Field(default_factory=dict)
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    scores: list[float] = Field(default_factory=list)


class RetrievalResult(StrictSchema):
    query: RetrievalQuery
    evidence: list[EvidenceObject]
    stats: RetrievalStats


class KnowledgeSearchRequest(StrictSchema):
    query: str = Field(min_length=1, max_length=4000)
    purpose: RetrievalPurpose
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, Any] = Field(default_factory=dict)
    mode: RetrievalMode = RetrievalMode.DIAGNOSTIC
