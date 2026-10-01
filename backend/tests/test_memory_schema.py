from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.memory import EquipmentMemoryRecord, MemorySourceType, MemoryStatus, MemoryType


def test_memory_schema_preserves_source_fact_classification() -> None:
    record = EquipmentMemoryRecord(
        memory_id="memory-1", equipment_id="rig-a", memory_type=MemoryType.DIAGNOSIS,
        source_type=MemorySourceType.AGENT, source_id="run-1", status=MemoryStatus.INFERRED,
        summary="An inferred candidate, not a confirmed equipment fact.", structured_data={},
        event_time=datetime.now(UTC), recorded_at=datetime.now(UTC),
    )
    assert record.status == MemoryStatus.INFERRED
    assert record.source_type == MemorySourceType.AGENT


def test_memory_schema_rejects_naive_timestamps() -> None:
    with pytest.raises(ValidationError):
        EquipmentMemoryRecord(
            memory_id="memory-1", equipment_id="rig-a", memory_type=MemoryType.ANALYSIS,
            source_type=MemorySourceType.ML_MODEL, source_id="run-1", status=MemoryStatus.MEASURED,
            summary="Measured analysis", event_time=datetime.now(), recorded_at=datetime.now(),
        )
