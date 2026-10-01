"""Deterministic, bounded equipment-history context selection."""

from __future__ import annotations

from app.memory.repository import EquipmentMemoryRepository
from app.memory.schemas import EquipmentMemoryContext, MemoryStatus, MemoryType


def select_relevant_context(
    repository: EquipmentMemoryRepository,
    equipment_id: str,
    *,
    operating_condition: str | None = None,
    recent_limit: int = 5,
) -> EquipmentMemoryContext:
    records = repository.list_records(equipment_id, limit=100)

    def select(memory_type: MemoryType, limit: int = recent_limit):
        selected = [item for item in records if item.memory_type == memory_type]
        if operating_condition:
            same_condition = [
                item for item in selected
                if item.structured_data.get("operating_condition") == operating_condition
            ]
            if same_condition:
                selected = same_condition
        return selected[:limit]

    measurements = select(MemoryType.MEASUREMENT)
    analyses = select(MemoryType.ANALYSIS)
    diagnoses = select(MemoryType.DIAGNOSIS)
    observations = select(MemoryType.HUMAN_OBSERVATION)
    unresolved = [
        item for item in records
        if item.memory_type in {MemoryType.DIAGNOSIS, MemoryType.ACTION}
        and item.status == MemoryStatus.INFERRED
    ][:recent_limit]
    maintenance = repository.list_maintenance(equipment_id, limit=recent_limit)
    used = [*measurements, *analyses, *diagnoses, *observations, *unresolved]
    memory_used_ids = list(dict.fromkeys(item.memory_id for item in used))
    return EquipmentMemoryContext(
        equipment_id=equipment_id,
        recent_measurements=measurements,
        recent_analyses=analyses,
        previous_diagnoses=diagnoses,
        human_observations=observations,
        maintenance_history=maintenance,
        unresolved_items=unresolved,
        memory_used_ids=memory_used_ids,
    )
