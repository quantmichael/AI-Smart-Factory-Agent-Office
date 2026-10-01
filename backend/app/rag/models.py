"""Traceable document and chunk contracts for the bearing knowledge pack."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from app.domain.schemas.common import StrictSchema


class IngestionStatus(StrEnum):
    READY = "READY"
    MISSING = "MISSING"
    INVALID = "INVALID"
    UNSUPPORTED = "UNSUPPORTED"
    LICENSE_REVIEW = "LICENSE_REVIEW"
    INGESTED = "INGESTED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class KnowledgeDocument(StrictSchema):
    document_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    knowledge_pack_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    publisher: str = Field(min_length=1)
    document_type: str = Field(min_length=1)
    source_tier: int = Field(ge=1, le=4)
    rag_roles: list[str]
    official_url: str = Field(min_length=1)
    local_path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    version: str = Field(min_length=1)
    license: str
    license_status: str
    ingestion_status: IngestionStatus
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedBlock(StrictSchema):
    page: int | None = Field(default=None, ge=1)
    section: str | None = None
    text: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeChunk(StrictSchema):
    knowledge_pack_id: str
    document_id: str
    chunk_id: str
    source_id: str
    title: str
    publisher: str
    document_type: str
    source_tier: int
    rag_roles: list[str]
    page: int | None = None
    section: str | None = None
    content: str = Field(min_length=1)
    equipment_type: str = "rotating_machinery"
    component: str = "bearing"
    fault_type: str | None = None
    bearing_id: str | None = None
    operating_condition: str | None = None
    official_url: str
    sha256: str
    document_version: str
    license_status: str
    metadata: dict[str, Any] = Field(default_factory=dict)
