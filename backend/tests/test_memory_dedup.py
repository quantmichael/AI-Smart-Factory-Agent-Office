from app.memory import EquipmentMemoryRepository
from tests.test_memory_repository import make_record


def test_same_source_is_upserted_not_duplicated(tmp_path) -> None:
    repository = EquipmentMemoryRepository(tmp_path / "memory.sqlite3")
    repository.upsert(make_record(summary="first"))
    repository.upsert(make_record(summary="updated"))
    records = repository.list_records("rig-a")
    assert len(records) == 1
    assert records[0].summary == "updated"
