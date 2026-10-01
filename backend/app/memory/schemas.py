"""Traceable schemas for equipment memory and explicit maintenance records."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator

from app.domain.schemas.common import StrictSchema


class MemoryType(StrEnum):
    MEASUREMENT = "MEASUREMENT"
    ANALYSIS = "ANALYSIS"
    DIAGNOSIS = "DIAGNOSIS"
    INSPECTION = "INSPECTION"
    HUMAN_OBSERVATION = "HUMAN_OBSERVATION"
    ACTION = "ACTION"
    MAINTENANCE = "MAINTENANCE"
    OUTCOME = "OUTCOME"


class MemorySourceType(StrEnum):
    SENSOR = "sensor"
    ML_MODEL = "ml_model"
    VISION_MODEL = "vision_model"
    AGENT = "agent"
    HUMAN = "human"
    MAINTENANCE_RECORD = "maintenance_record"
    SYSTEM = "system"


class MemoryStatus(StrEnum):
    OBSERVED = "OBSERVED"
    MEASURED = "MEASURED"
    INFERRED = "INFERRED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value


class EquipmentMemoryRecord(StrictSchema):
    memory_id: str = Field(min_length=1)
    equipment_id: str = Field(min_length=1)
    memory_type: MemoryType
    source_type: MemorySourceType
    source_id: str = Field(min_length=1)
    status: MemoryStatus
    summary: str = Field(min_length=1)
    structured_data: dict[str, Any] = Field(default_factory=dict)
    event_time: datetime
    recorded_at: datetime
    memory_version: int = Field(default=1, ge=1)

    _event_time_aware = field_validator("event_time")(_aware)
    _recorded_at_aware = field_validator("recorded_at")(_aware)


class MaintenanceRecordCreate(StrictSchema):
    maintenance_type: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=4000)
    performed_at: datetime
    performed_by_role: str | None = Field(default=None, max_length=100)
    related_run_id: str | None = Field(default=None, max_length=200)
    outcome: str | None = Field(default=None, max_length=2000)
    source_label: str = Field(default="operator_submitted", min_length=1, max_length=100)

    _performed_at_aware = field_validator("performed_at")(_aware)


class MaintenanceRecord(MaintenanceRecordCreate):
    maintenance_id: str
    equipment_id: str
    recorded_at: datetime

    _recorded_at_aware = field_validator("recorded_at")(_aware)


class EquipmentMemoryContext(StrictSchema):
    equipment_id: str
    recent_measurements: list[EquipmentMemoryRecord] = Field(default_factory=list)
    recent_analyses: list[EquipmentMemoryRecord] = Field(default_factory=list)
    previous_diagnoses: list[EquipmentMemoryRecord] = Field(default_factory=list)
    human_observations: list[EquipmentMemoryRecord] = Field(default_factory=list)
    maintenance_history: list[MaintenanceRecord] = Field(default_factory=list)
    unresolved_items: list[EquipmentMemoryRecord] = Field(default_factory=list)
    memory_used_ids: list[str] = Field(default_factory=list)


class TrendPoint(StrictSchema):
    memory_id: str
    run_id: str
    measurement_id: str
    event_time: datetime
    operating_condition: str | None = None
    analysis_status: str | None = None
    predicted_class: str | None = None
    rms: float | None = None
    kurtosis: float | None = None


class EquipmentTrend(StrictSchema):
    equipment_id: str
    points: list[TrendPoint]
    abnormal_count: int = Field(ge=0)
    note: str


class MemoryHistory(StrictSchema):
    equipment_id: str
    records: list[EquipmentMemoryRecord]
    maintenance: list[MaintenanceRecord]
    trend: EquipmentTrend
