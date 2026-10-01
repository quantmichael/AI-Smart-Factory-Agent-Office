from datetime import UTC, datetime

from app.memory import EquipmentMemoryRecord, EquipmentMemoryRepository, MemorySourceType, MemoryStatus, MemoryType


def make_record(equipment_id: str = "rig-a", summary: str = "summary") -> EquipmentMemoryRecord:
    return EquipmentMemoryRecord(
        memory_id=f"memory-{equipment_id}", equipment_id=equipment_id,
        memory_type=MemoryType.ANALYSIS, source_type=MemorySourceType.ML_MODEL,
        source_id="run-1", status=MemoryStatus.MEASURED, summary=summary,
        structured_data={"run_id": "run-1"}, event_time=datetime.now(UTC),
        recorded_at=datetime.now(UTC),
    )


def test_repository_round_trip_and_filter(tmp_path) -> None:
    repository = EquipmentMemoryRepository(tmp_path / "memory.sqlite3")
    repository.upsert(make_record())
    records = repository.list_records("rig-a", memory_types={MemoryType.ANALYSIS})
    assert len(records) == 1
    assert records[0].structured_data["run_id"] == "run-1"
