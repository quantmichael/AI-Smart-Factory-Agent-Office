"""Shared domain contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain.schemas import (
    AgentEvent,
    AnalysisResult,
    EvidenceObject,
    MeasurementRef,
    WorkflowStatus,
)


def test_measurement_metadata_is_not_shared() -> None:
    first = MeasurementRef(measurement_id="m-1", equipment_id="e-1", source="test")
    second = MeasurementRef(measurement_id="m-2", equipment_id="e-1", source="test")

    first.metadata["key"] = "value"

    assert second.metadata == {}


def test_analysis_result_accepts_valid_contract() -> None:
    result = AnalysisResult(
        analysis_id="a-1",
        measurement_id="m-1",
        model_id="model-1",
        status="abnormal",
        predicted_class="damaged",
        confidence=0.91,
        signal_features={"rms": 1.2},
    )

    assert result.status.value == "abnormal"
    assert result.anomaly_score is None


@pytest.mark.parametrize("status", ["unknown", "ABNORMAL", "healthy"])
def test_analysis_result_rejects_invalid_status(status: str) -> None:
    with pytest.raises(ValidationError):
        AnalysisResult(
            analysis_id="a-1",
            measurement_id="m-1",
            model_id="model-1",
            status=status,
            predicted_class="damaged",
        )


def test_analysis_result_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        AnalysisResult(
            analysis_id="a-1",
            measurement_id="m-1",
            model_id="model-1",
            status="abnormal",
            predicted_class="damaged",
            confidence=1.1,
        )


def test_evidence_uses_canonical_content_field() -> None:
    evidence = EvidenceObject(
        evidence_id="ev-1",
        document_id="doc-1",
        chunk_id="chunk-1",
        title="Technical guide",
        publisher="Publisher",
        document_type="diagnostic_guide",
        source_tier=2,
        content="Retrieved source content.",
    )

    assert evidence.content == "Retrieved source content."
    assert "text" not in evidence.model_dump()


def test_evidence_rejects_unknown_text_alias() -> None:
    with pytest.raises(ValidationError):
        EvidenceObject(
            evidence_id="ev-1",
            document_id="doc-1",
            chunk_id="chunk-1",
            title="Technical guide",
            publisher="Publisher",
            document_type="diagnostic_guide",
            source_tier=2,
            text="Non-canonical field.",
        )


def test_agent_event_requires_timezone_aware_timestamp() -> None:
    valid = AgentEvent(
        event_id="event-1",
        run_id="run-1",
        sequence=1,
        event_type="node_started",
        node="initialize_run",
        agent_role="SYSTEM",
        message="Run started.",
        created_at=datetime.now(UTC),
    )

    assert valid.created_at.utcoffset() is not None

    with pytest.raises(ValidationError):
        AgentEvent(
            event_id="event-2",
            run_id="run-1",
            sequence=2,
            event_type="node_completed",
            node="initialize_run",
            agent_role="SYSTEM",
            message="Run initialized.",
            created_at=datetime.now(),
        )


def test_workflow_status_has_only_approved_top_level_values() -> None:
    assert {status.value for status in WorkflowStatus} == {
        "CREATED",
        "RUNNING",
        "WAITING",
        "COMPLETED",
        "FAILED",
    }
