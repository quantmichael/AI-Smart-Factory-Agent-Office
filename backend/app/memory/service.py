"""Application service for recording and selecting equipment history."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
from typing import Any
from uuid import uuid4

from app.memory.repository import EquipmentMemoryRepository
from app.memory.schemas import (
    EquipmentMemoryRecord,
    EquipmentTrend,
    MaintenanceRecord,
    MaintenanceRecordCreate,
    MemoryHistory,
    MemorySourceType,
    MemoryStatus,
    MemoryType,
    TrendPoint,
)
from app.memory.selectors import select_relevant_context
from app.memory.summarizer import action_summary, analysis_summary, diagnosis_summary, inspection_summary


class EquipmentMemoryService:
    def __init__(self, repository: EquipmentMemoryRepository) -> None:
        self.repository = repository

    @staticmethod
    def _memory_id(equipment_id: str, memory_type: MemoryType, source_id: str) -> str:
        value = f"{equipment_id}:{memory_type.value}:{source_id}"
        return "memory_" + hashlib.sha256(value.encode()).hexdigest()[:20]

    def _record(
        self,
        *,
        equipment_id: str,
        memory_type: MemoryType,
        source_type: MemorySourceType,
        source_id: str,
        status: MemoryStatus,
        summary: str,
        structured_data: dict[str, Any],
        event_time: datetime,
    ) -> EquipmentMemoryRecord:
        now = datetime.now(UTC)
        return self.repository.upsert(
            EquipmentMemoryRecord(
                memory_id=self._memory_id(equipment_id, memory_type, source_id),
                equipment_id=equipment_id,
                memory_type=memory_type,
                source_type=source_type,
                source_id=source_id,
                status=status,
                summary=summary,
                structured_data=structured_data,
                event_time=event_time,
                recorded_at=now,
            )
        )

    def record_run_memory(self, state: dict[str, Any]) -> list[EquipmentMemoryRecord]:
        if state.get("workflow_status") != "COMPLETED" or not state.get("analysis_result"):
            return []
        equipment_id, run_id = state["equipment_id"], state["run_id"]
        report = state.get("final_report") or {}
        event_time = datetime.fromisoformat(report.get("created_at")) if report.get("created_at") else datetime.now(UTC)
        condition = state.get("operating_condition", {}).get("code")
        analysis = state["analysis_result"]
        base = {"run_id": run_id, "measurement_id": state["measurement_id"], "operating_condition": condition}
        records = [
            self._record(
                equipment_id=equipment_id, memory_type=MemoryType.MEASUREMENT,
                source_type=MemorySourceType.SENSOR, source_id=run_id,
                status=MemoryStatus.MEASURED,
                summary=f"Measurement {state['measurement_id']} was processed under condition {condition or 'unknown'}.",
                structured_data={**base, "measurement_ref": state.get("measurement_ref", {})}, event_time=event_time,
            ),
            self._record(
                equipment_id=equipment_id, memory_type=MemoryType.ANALYSIS,
                source_type=MemorySourceType.ML_MODEL, source_id=run_id,
                status=MemoryStatus.MEASURED, summary=analysis_summary(state),
                structured_data={**base, "analysis_id": analysis["analysis_id"], "status": analysis["status"],
                    "predicted_class": analysis["predicted_class"], "model_id": analysis["model_id"],
                    "confidence": analysis.get("confidence"), "signal_features": analysis.get("signal_features", {})},
                event_time=event_time,
            ),
        ]
        if state.get("diagnosis_candidates"):
            records.append(self._record(
                equipment_id=equipment_id, memory_type=MemoryType.DIAGNOSIS,
                source_type=MemorySourceType.AGENT, source_id=run_id,
                status=MemoryStatus.INFERRED, summary=diagnosis_summary(state),
                structured_data={**base, "evidence_status": state.get("evidence_status"),
                    "candidates": state["diagnosis_candidates"]}, event_time=event_time,
            ))
        if state.get("inspection_plan"):
            records.append(self._record(
                equipment_id=equipment_id, memory_type=MemoryType.INSPECTION,
                source_type=MemorySourceType.AGENT, source_id=run_id,
                status=MemoryStatus.INFERRED, summary=inspection_summary(state),
                structured_data={
                    **base,
                    "inspection_plan": state["inspection_plan"],
                    "inspection_image_ids": state.get("inspection_image_ids", []),
                    "visual_observations": state.get("visual_observations", []),
                }, event_time=event_time,
            ))
        for result in state.get("visual_observations", []):
            records.append(self._record(
                equipment_id=equipment_id,
                memory_type=MemoryType.INSPECTION,
                source_type=MemorySourceType.VISION_MODEL,
                source_id=result["image_id"],
                status=MemoryStatus.OBSERVED,
                summary=(
                    f"Inspection image {result['image_id']} produced "
                    f"{len(result.get('observations', []))} direct observation(s) with "
                    f"quality {result.get('quality', 'unknown')}."
                ),
                structured_data={
                    **base,
                    "image_id": result["image_id"],
                    "quality": result.get("quality"),
                    "observations": result.get("observations", []),
                    "limitations": result.get("limitations", []),
                },
                event_time=datetime.fromisoformat(result["created_at"]),
            ))
        if state.get("recommended_actions"):
            records.append(self._record(
                equipment_id=equipment_id, memory_type=MemoryType.ACTION,
                source_type=MemorySourceType.AGENT, source_id=run_id,
                status=MemoryStatus.INFERRED, summary=action_summary(state),
                structured_data={**base, "recommended_actions": state["recommended_actions"],
                    "human_interactions": state.get("human_interactions", [])}, event_time=event_time,
            ))
        for index, observation in enumerate(state.get("human_observations", [])):
            records.append(self._record(
                equipment_id=equipment_id, memory_type=MemoryType.HUMAN_OBSERVATION,
                source_type=MemorySourceType.HUMAN, source_id=f"{run_id}:{index}",
                status=MemoryStatus.OBSERVED,
                summary=f"Human observation recorded for {observation.get('type', 'field input')}.",
                structured_data={**base, "observation": observation},
                event_time=datetime.fromisoformat(observation["recorded_at"]),
            ))
        records.append(self._record(
            equipment_id=equipment_id, memory_type=MemoryType.OUTCOME,
            source_type=MemorySourceType.SYSTEM, source_id=run_id,
            status=MemoryStatus.CONFIRMED, summary="Diagnostic workflow completed and a final report was generated.",
            structured_data={**base, "evidence_status": state.get("evidence_status"),
                "memory_used_ids": state.get("memory_used_ids", [])}, event_time=event_time,
        ))
        return records

    def record_maintenance(
        self, equipment_id: str, create: MaintenanceRecordCreate
    ) -> MaintenanceRecord:
        now = datetime.now(UTC)
        record = MaintenanceRecord(
            maintenance_id=f"maintenance_{uuid4().hex}", equipment_id=equipment_id,
            recorded_at=now, **create.model_dump(),
        )
        self.repository.save_maintenance(record)
        self._record(
            equipment_id=equipment_id, memory_type=MemoryType.MAINTENANCE,
            source_type=MemorySourceType.MAINTENANCE_RECORD, source_id=record.maintenance_id,
            status=MemoryStatus.CONFIRMED,
            summary=f"Explicit maintenance record: {record.maintenance_type} — {record.description}",
            structured_data=record.model_dump(mode="json"), event_time=record.performed_at,
        )
        return record

    def get_relevant_context(self, equipment_id: str, *, operating_condition: str | None = None):
        return select_relevant_context(
            self.repository, equipment_id, operating_condition=operating_condition
        )

    def get_history(self, equipment_id: str, *, limit: int = 100) -> MemoryHistory:
        records = self.repository.list_records(equipment_id, limit=limit)
        maintenance = self.repository.list_maintenance(equipment_id)
        analyses = [item for item in reversed(records) if item.memory_type == MemoryType.ANALYSIS]
        points = [TrendPoint(
            memory_id=item.memory_id,
            run_id=str(item.structured_data.get("run_id", "")),
            measurement_id=str(item.structured_data.get("measurement_id", "")),
            event_time=item.event_time,
            operating_condition=item.structured_data.get("operating_condition"),
            analysis_status=item.structured_data.get("status"),
            predicted_class=item.structured_data.get("predicted_class"),
            rms=item.structured_data.get("signal_features", {}).get("rms"),
            kurtosis=item.structured_data.get("signal_features", {}).get("kurtosis"),
        ) for item in analyses]
        trend = EquipmentTrend(
            equipment_id=equipment_id, points=points,
            abnormal_count=sum(item.analysis_status == "abnormal" for item in points),
            note="Feature values must be compared with operating condition; no degradation claim is inferred.",
        )
        return MemoryHistory(
            equipment_id=equipment_id, records=records, maintenance=maintenance, trend=trend
        )
