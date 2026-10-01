from app.memory import EquipmentMemoryRepository, EquipmentMemoryService
from tests.agent_helpers import build_fake_agent_service
from tests.test_memory_context import completed_state


def test_rag_evidence_and_equipment_history_remain_separate_context_sections(tmp_path) -> None:
    memory = EquipmentMemoryService(EquipmentMemoryRepository(tmp_path / "memory.sqlite3"))
    previous = completed_state("previous-run", condition="N15_M07_F10")
    previous["equipment_id"] = "fake-rig"
    memory.record_run_memory(previous)
    workflow, _, _ = build_fake_agent_service(tmp_path / "checkpoint.sqlite3", status="abnormal")
    workflow.dependencies.memory_service = memory
    try:
        state = workflow.start_run("fake:measurement:1", run_id="current-run")
        assert state["rag_evidence"]
        assert state["equipment_memory"]["memory_used_ids"]
        assert all("evidence_id" in item and "memory_id" not in item for item in state["rag_evidence"])
        memory_records = state["equipment_memory"]["recent_analyses"]
        assert all("memory_id" in item and "evidence_id" not in item for item in memory_records)
        diagnose_event = next(
            item for item in state["events"]
            if item["node"] == "diagnose" and item["event_type"] == "node_completed"
        )
        assert diagnose_event["payload"]["context_sections"] == [
            "CURRENT_SENSOR_ANALYSIS", "VISUAL_OBSERVATIONS", "TECHNICAL_EVIDENCE",
            "EQUIPMENT_MEMORY", "HUMAN_OBSERVATIONS",
        ]
    finally:
        workflow.close()
