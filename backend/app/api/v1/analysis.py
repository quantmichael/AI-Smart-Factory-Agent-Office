"""Versioned endpoint for real model inference by measurement ID."""

from __future__ import annotations

from threading import Lock
from typing import Any

from fastapi import APIRouter, Depends, Query
import numpy as np
from pydantic import Field

from app.core.config import get_settings, resolve_runtime_path
from app.data.adapters.paderborn import PaderbornDatasetAdapter
from app.domain.schemas import AnalysisRequest, AnalysisResult, ErrorResponse
from app.domain.schemas.common import StrictSchema
from app.services.analysis import AnalysisApplicationService, build_analysis_service


router = APIRouter(tags=["analysis"])
_service: AnalysisApplicationService | None = None
_service_lock = Lock()


class PreviewPoint(StrictSchema):
    time: float
    value: float


class MeasurementPreview(StrictSchema):
    measurement_id: str
    equipment_id: str
    source: str
    bearing_id: str
    operating_condition: dict[str, Any]
    run_index: int
    channel: str
    original_sample_count: int = Field(ge=1)
    points: list[PreviewPoint]
    operating_signals: dict[str, list[PreviewPoint]] = Field(default_factory=dict)


def get_analysis_service() -> AnalysisApplicationService:
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                settings = get_settings()
                _service = build_analysis_service(
                    dataset_root=resolve_runtime_path(settings.paderborn_data_root),
                    artifact_root=resolve_runtime_path(settings.ml_artifact_root),
                    active_model_id=settings.active_ml_model_id,
                    adapter_factory=PaderbornDatasetAdapter,
                )
    return _service


@router.post(
    "/analysis",
    response_model=AnalysisResult,
    responses={
        404: {"model": ErrorResponse, "description": "Measurement or model not found"},
        422: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Inference pipeline failure"},
    },
    summary="Analyze one indexed measurement",
)
def create_analysis(
    request: AnalysisRequest,
    service: AnalysisApplicationService = Depends(get_analysis_service),
) -> AnalysisResult:
    return service.analyze(request.measurement_id, request.model_id)


@router.get(
    "/measurements/{measurement_id}/preview",
    response_model=MeasurementPreview,
    responses={404: {"model": ErrorResponse, "description": "Measurement not found"}},
    summary="Return a bounded waveform preview and measurement metadata",
)
def get_measurement_preview(
    measurement_id: str,
    max_points: int = Query(default=160, ge=32, le=512),
    service: AnalysisApplicationService = Depends(get_analysis_service),
) -> MeasurementPreview:
    measurement = service.adapter.load_measurement(measurement_id)
    channel = "vibration_1"
    if channel not in measurement.signals:
        channel = next(iter(measurement.signals))
    signal = measurement.signals[channel]
    count = len(signal.values)
    indices = np.unique(np.linspace(0, count - 1, min(max_points, count), dtype=int))
    preview_times = signal.time[indices].astype(np.float64, copy=False)
    operating_signals: dict[str, list[PreviewPoint]] = {}
    for signal_name in ("speed", "torque", "force"):
        operating_signal = measurement.signals.get(signal_name)
        if operating_signal is None:
            continue
        # Sample each channel on the vibration preview's actual timestamps. The
        # source channels have different sample counts, so raw array indices do
        # not correspond; interpolation uses their recorded time axes instead.
        values = np.interp(
            preview_times,
            operating_signal.time.astype(np.float64, copy=False),
            operating_signal.values.astype(np.float64, copy=False),
        )
        operating_signals[signal_name] = [
            PreviewPoint(time=float(time), value=float(value))
            for time, value in zip(preview_times, values, strict=True)
        ]
    summary = measurement.summary
    return MeasurementPreview(
        measurement_id=summary.measurement_id,
        equipment_id=summary.equipment_id,
        source=summary.source,
        bearing_id=summary.bearing_id,
        operating_condition=summary.operating_condition.model_dump(mode="json"),
        run_index=summary.run_index,
        channel=channel,
        original_sample_count=count,
        points=[
            PreviewPoint(time=float(signal.time[index]), value=float(signal.values[index]))
            for index in indices
        ],
        operating_signals=operating_signals,
    )
