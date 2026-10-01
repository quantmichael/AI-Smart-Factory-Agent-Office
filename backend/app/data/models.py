"""Dataset-independent measurement and validation models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
from pydantic import Field

from app.domain.schemas.common import StrictSchema


class OperatingCondition(StrictSchema):
    """Operating values verified by the official Paderborn condition table."""

    code: str = Field(min_length=1)
    rpm: int | None = Field(default=None, gt=0)
    load_torque_nm: float | None = Field(default=None, ge=0)
    radial_force_n: int | None = Field(default=None, ge=0)
    temperature_c: float | None = None


class GroundTruth(StrictSchema):
    """Ground truth supported by an acquired bearing fact sheet."""

    state: Literal["healthy", "damaged", "unknown"]
    fault_type: str | None = None
    damage_location: str | None = None
    damage_mechanism: str | None = None
    evidence_reference: str | None = None


class MeasurementSummary(StrictSchema):
    """Lazy index record; it never contains raw signal arrays."""

    measurement_id: str = Field(min_length=1)
    equipment_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    bearing_id: str = Field(min_length=1)
    operating_condition: OperatingCondition
    run_index: int = Field(ge=1)
    ground_truth: GroundTruth
    source_reference: str = Field(min_length=1)


class SamplingMetadata(StrictSchema):
    """Sampling facts associated with one raw channel."""

    raster: str = Field(min_length=1)
    nominal_rate_hz: float | None = Field(default=None, gt=0)
    observed_rate_hz: float | None = Field(default=None, gt=0)
    sample_count: int = Field(ge=1)
    duration_sec: float | None = Field(default=None, gt=0)
    uniform_time_axis: bool | None = None


@dataclass(frozen=True, slots=True)
class SignalSeries:
    """One raw signal and its corresponding time axis."""

    name: str
    values: np.ndarray
    time: np.ndarray
    sampling: SamplingMetadata
    raw_metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class StandardMeasurement:
    """Dataset-independent in-memory measurement with lazy-loaded arrays."""

    summary: MeasurementSummary
    signals: dict[str, SignalSeries]
    metadata: dict[str, Any]


class InvalidMeasurement(StrictSchema):
    """Validation failure tied to a stable measurement ID."""

    measurement_id: str
    source_reference: str
    errors: list[str]


class DatasetValidationResult(StrictSchema):
    """Serializable validation and dataset statistics artifact."""

    status: Literal["pass", "fail"]
    measurement_count: int
    bearing_count: int
    healthy_count: int
    damaged_count: int
    unknown_count: int
    operating_condition_distribution: dict[str, int]
    signal_channel_distribution: dict[str, int]
    signal_length_distribution: dict[str, dict[str, int]]
    missing_metadata_count: int
    invalid_measurement_count: int
    invalid_measurements: list[InvalidMeasurement]
    warnings: list[str]
    index_build_seconds: float = Field(ge=0)
    validation_seconds: float = Field(ge=0)
