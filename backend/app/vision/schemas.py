"""Strict contracts for inspection images and observation-only vision output."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator

from app.domain.schemas.common import StrictSchema


class ImageQuality(StrEnum):
    USABLE = "USABLE"
    LOW_QUALITY = "LOW_QUALITY"
    UNUSABLE = "UNUSABLE"


class InspectionImageRecord(StrictSchema):
    image_id: str
    run_id: str | None = None
    equipment_id: str
    file_ref: str
    original_filename: str
    mime_type: str
    size_bytes: int = Field(gt=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    captured_at: datetime | None = None
    uploaded_at: datetime
    description: str | None = Field(default=None, max_length=500)

    @field_validator("captured_at", "uploaded_at")
    @classmethod
    def timestamps_are_aware(cls, value: datetime | None):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("image timestamps must be timezone-aware")
        return value


class PublicInspectionImage(StrictSchema):
    """Inspection image metadata safe to return from public HTTP APIs."""

    image_id: str
    run_id: str | None = None
    equipment_id: str
    original_filename: str
    mime_type: str
    size_bytes: int = Field(gt=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    captured_at: datetime | None = None
    uploaded_at: datetime
    description: str | None = Field(default=None, max_length=500)
    image_url: str

    @field_validator("captured_at", "uploaded_at")
    @classmethod
    def timestamps_are_aware(cls, value: datetime | None):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("image timestamps must be timezone-aware")
        return value


class VisualObservationItem(StrictSchema):
    observation_id: str
    category: str
    description: str
    confidence_level: str


class VisualObservation(StrictSchema):
    image_id: str
    provider: str
    model: str
    observations: list[VisualObservationItem] = Field(default_factory=list)
    visible_components: list[str] = Field(default_factory=list)
    quality: ImageQuality
    limitations: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    analysis_error: str | None = None
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def created_at_is_aware(cls, value: datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value


class PublicInspectionImageResult(StrictSchema):
    image: PublicInspectionImage
    observation: VisualObservation | None = None


class RunInspectionImageList(StrictSchema):
    run_id: str
    images: list[PublicInspectionImageResult] = Field(default_factory=list)
