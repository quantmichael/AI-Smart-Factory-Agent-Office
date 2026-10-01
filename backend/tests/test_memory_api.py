from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.v1.equipment import get_equipment_memory_service
from app.main import app
from app.memory import EquipmentMemoryRepository, EquipmentMemoryService


def test_memory_and_explicit_maintenance_api(tmp_path) -> None:
    service = EquipmentMemoryService(EquipmentMemoryRepository(tmp_path / "memory.sqlite3"))
    app.dependency_overrides[get_equipment_memory_service] = lambda: service
    try:
        with TestClient(app) as client:
            empty = client.get("/api/v1/equipment/rig-a/memory")
            assert empty.status_code == 200
            assert empty.json()["memory_used_ids"] == []

            created = client.post(
                "/api/v1/equipment/rig-a/maintenance",
                json={
                    "maintenance_type": "inspection",
                    "description": "Operator explicitly recorded this inspection.",
                    "performed_at": datetime.now(UTC).isoformat(),
                },
            )
            assert created.status_code == 201
            assert created.json()["source_label"] == "operator_submitted"

            history = client.get("/api/v1/equipment/rig-a/history")
            assert history.status_code == 200
            assert len(history.json()["maintenance"]) == 1
            assert history.json()["records"][0]["memory_type"] == "MAINTENANCE"
    finally:
        app.dependency_overrides.clear()
