from app.memory import EquipmentMemoryRepository
from tests.test_memory_repository import make_record


def test_equipment_history_is_strictly_isolated(tmp_path) -> None:
    repository = EquipmentMemoryRepository(tmp_path / "memory.sqlite3")
    repository.upsert(make_record("rig-a"))
    repository.upsert(make_record("rig-b"))
    assert {item.equipment_id for item in repository.list_records("rig-a")} == {"rig-a"}
    assert {item.equipment_id for item in repository.list_records("rig-b")} == {"rig-b"}
