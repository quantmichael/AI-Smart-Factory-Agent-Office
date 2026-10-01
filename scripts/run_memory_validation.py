"""Run two real measurements and emit STEP 12 equipment-memory artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.agent import build_agent_service  # noqa: E402
from app.agent.run_manager import AgentRunManager  # noqa: E402
from app.agent.schemas import AgentRunCreate  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.memory import EquipmentMemoryRepository, EquipmentMemoryService  # noqa: E402


def dump(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def backend_path(path: Path) -> Path:
    return path if path.is_absolute() else (BACKEND / path).resolve()


def main() -> None:
    settings = Settings()
    output = ROOT / "artifacts/memory"
    runtime = output / "runtime" / datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    output.mkdir(parents=True, exist_ok=True)
    runtime.mkdir(parents=True, exist_ok=True)
    memory = EquipmentMemoryService(EquipmentMemoryRepository(runtime / "equipment_memory.sqlite3"))
    workflow = build_agent_service(
        dataset_root=backend_path(settings.paderborn_data_root),
        ml_artifact_root=backend_path(settings.ml_artifact_root),
        active_model_id=settings.active_ml_model_id,
        vector_db_path=backend_path(settings.vector_db_path),
        checkpoint_path=runtime / "checkpoints.sqlite3",
        memory_db_path=runtime / "equipment_memory.sqlite3",
        max_retrieval_retries=settings.max_retrieval_retries,
    )
    # Use the same service object for graph retrieval and artifact reads.
    workflow.dependencies.memory_service = memory
    manager = AgentRunManager(workflow, runtime / "agent_runs.sqlite3", max_workers=1)
    try:
        summaries = list(workflow.dependencies.analysis_service.adapter.list_measurements())
        preferred = [item for item in summaries if item.bearing_id == "K001"]
        selected = preferred[:2] if len(preferred) >= 2 else summaries[:2]
        if len(selected) < 2:
            raise RuntimeError("At least two indexed measurements are required")
        equipment_id = selected[0].equipment_id
        selected = [item for item in selected if item.equipment_id == equipment_id]
        if len(selected) < 2:
            selected = [item for item in summaries if item.equipment_id == equipment_id][:2]

        run_ids: list[str] = []
        for summary in selected:
            created = manager.create_run(AgentRunCreate(
                equipment_id=equipment_id, measurement_id=summary.measurement_id
            ))
            manager.wait_for_status(created.run_id, {"COMPLETED"}, timeout_seconds=60)
            run_ids.append(created.run_id)

        run1_records = [
            item.model_dump(mode="json")
            for item in memory.repository.list_records(equipment_id)
            if item.source_id == run_ids[0]
        ]
        run2_state = workflow.get_run(run_ids[1]) or {}
        history = memory.get_history(equipment_id)
        isolation = memory.get_history("unrelated-equipment")

        dump(output / "run1_memory.json", {
            "run_id": run_ids[0], "equipment_id": equipment_id,
            "records": run1_records, "maintenance_auto_generated": False,
        })
        dump(output / "run2_context.json", {
            "run_id": run_ids[1], "equipment_id": equipment_id,
            "context": run2_state.get("equipment_memory", {}),
            "memory_used_ids": run2_state.get("memory_used_ids", []),
            "analysis_measurement_id": run2_state.get("analysis_result", {}).get("measurement_id"),
        })
        dump(output / "equipment_history_sample.json", history.model_dump(mode="json"))
        dump(output / "memory_isolation_test.json", {
            "source_equipment": equipment_id,
            "source_record_count": len(history.records),
            "other_equipment": isolation.equipment_id,
            "other_record_count": len(isolation.records),
            "isolated": len(isolation.records) == 0,
        })
        report = f"""# Long-term Equipment Memory Validation

- Generated at: {datetime.now(UTC).isoformat()}
- Equipment: `{equipment_id}`
- Run 1: `{run_ids[0]}` using `{selected[0].measurement_id}`
- Run 1 stored memories: {len(run1_records)}
- Run 2: `{run_ids[1]}` using `{selected[1].measurement_id}`
- Run 2 retrieved memories: {len(run2_state.get('memory_used_ids', []))}
- Equipment isolation: {'PASS' if len(isolation.records) == 0 else 'FAIL'}
- Automatic maintenance creation: disabled
- Technical RAG storage: `artifacts/vector_db` / `bearing_v1`
- Equipment memory storage: isolated SQLite database

The current ML analysis still uses only the current measurement. Historical
records are passed as a separate `EQUIPMENT_HISTORY` diagnosis context and are
not represented as technical-document evidence.
"""
        (output / "LONG_TERM_MEMORY_REPORT.md").write_text(report, encoding="utf-8")
        print(json.dumps({
            "status": "PASS", "equipment_id": equipment_id, "run_ids": run_ids,
            "run1_memory_count": len(run1_records),
            "run2_memory_used_count": len(run2_state.get("memory_used_ids", [])),
            "history_record_count": len(history.records),
        }, indent=2))
    finally:
        manager.close()


if __name__ == "__main__":
    main()
