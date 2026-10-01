from datetime import UTC, datetime

from app.memory import EquipmentMemoryRepository, EquipmentMemoryService, MaintenanceRecordCreate
from tests.test_memory_context import completed_state


def test_selector_prefers_same_operating_condition_and_includes_explicit_maintenance(tmp_path) -> None:
    service = EquipmentMemoryService(EquipmentMemoryRepository(tmp_path / "memory.sqlite3"))
    service.record_run_memory(completed_state("run-c1", condition="C1"))
    service.record_run_memory(completed_state("run-c2", condition="C2"))
    maintenance = service.record_maintenance(
        "rig-a",
        MaintenanceRecordCreate(
            maintenance_type="inspection",
            description="Operator explicitly recorded a lubrication inspection.",
            performed_at=datetime.now(UTC),
        ),
    )
    context = service.get_relevant_context("rig-a", operating_condition="C1")
    assert {item.structured_data["operating_condition"] for item in context.recent_analyses} == {"C1"}
    assert context.maintenance_history[0].maintenance_id == maintenance.maintenance_id
