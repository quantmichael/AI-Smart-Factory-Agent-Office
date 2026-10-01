"""Safe AnalysisResult adapter that never copies dataset ground truth."""

from __future__ import annotations

from app.data.models import MeasurementSummary
from app.domain.schemas import AnalysisResult
from app.rag.retrieval.models import RetrievalContext, RetrievalMode


def build_retrieval_context(
    analysis_result: AnalysisResult,
    measurement_metadata: MeasurementSummary | None = None,
    *,
    mode: RetrievalMode = RetrievalMode.DIAGNOSTIC,
) -> RetrievalContext:
    """Build operational context without reading or exposing GroundTruth fields."""

    metadata = analysis_result.metadata
    bearing_id = (
        measurement_metadata.bearing_id
        if measurement_metadata is not None
        else metadata.get("bearing_id")
    )
    operating_condition = (
        measurement_metadata.operating_condition.code
        if measurement_metadata is not None
        else metadata.get("operating_condition")
    )
    return RetrievalContext(
        analysis_id=analysis_result.analysis_id,
        measurement_id=analysis_result.measurement_id,
        status=analysis_result.status.value,
        predicted_class=analysis_result.predicted_class,
        confidence=analysis_result.confidence,
        signal_features=analysis_result.signal_features,
        bearing_id=str(bearing_id) if bearing_id else None,
        operating_condition=str(operating_condition) if operating_condition else None,
        mode=mode,
    )
