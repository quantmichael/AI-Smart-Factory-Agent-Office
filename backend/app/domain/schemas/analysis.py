"""Public request and error contracts for ML analysis."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.domain.schemas.common import StrictSchema


class AnalysisRequest(StrictSchema):
    measurement_id: str = Field(min_length=1, max_length=256)
    model_id: str | None = Field(default=None, min_length=1, max_length=128)


class ErrorDetail(StrictSchema):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(StrictSchema):
    error: ErrorDetail
