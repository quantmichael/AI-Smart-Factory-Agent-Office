"""Equipment history and explicit maintenance-record APIs."""

from __future__ import annotations

from threading import Lock

from fastapi import APIRouter, Depends, Query, status

from app.core.config import get_settings, resolve_runtime_path
from app.memory import (
    EquipmentMemoryContext,
    EquipmentMemoryRepository,
    EquipmentMemoryService,
    MaintenanceRecord,
    MaintenanceRecordCreate,
    MemoryHistory,
)


router = APIRouter(prefix="/equipment", tags=["equipment-memory"])
_service: EquipmentMemoryService | None = None
_lock = Lock()


def get_equipment_memory_service() -> EquipmentMemoryService:
    global _service
    if _service is None:
        with _lock:
            if _service is None:
                settings = get_settings()
                _service = EquipmentMemoryService(
                    EquipmentMemoryRepository(resolve_runtime_path(settings.equipment_memory_db_path))
                )
    return _service


@router.get("/{equipment_id}/history", response_model=MemoryHistory)
def get_equipment_history(
    equipment_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    service: EquipmentMemoryService = Depends(get_equipment_memory_service),
) -> MemoryHistory:
    return service.get_history(equipment_id, limit=limit)


@router.get("/{equipment_id}/memory", response_model=EquipmentMemoryContext)
def get_equipment_memory(
    equipment_id: str,
    operating_condition: str | None = None,
    service: EquipmentMemoryService = Depends(get_equipment_memory_service),
) -> EquipmentMemoryContext:
    return service.get_relevant_context(
        equipment_id, operating_condition=operating_condition
    )


@router.post(
    "/{equipment_id}/maintenance",
    response_model=MaintenanceRecord,
    status_code=status.HTTP_201_CREATED,
)
def create_maintenance_record(
    equipment_id: str,
    body: MaintenanceRecordCreate,
    service: EquipmentMemoryService = Depends(get_equipment_memory_service),
) -> MaintenanceRecord:
    """Store only a caller-supplied maintenance record; nothing is synthesized."""
    return service.record_maintenance(equipment_id, body)
