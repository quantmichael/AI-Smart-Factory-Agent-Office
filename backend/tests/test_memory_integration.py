from app.agent.run_manager import AgentRunManager
from app.agent.schemas import AgentRunCreate
from app.memory import EquipmentMemoryRepository, EquipmentMemoryService
from tests.agent_helpers import build_fake_agent_service


def test_second_run_loads_first_run_history_without_changing_ml_input(tmp_path) -> None:
    workflow, analysis, _ = build_fake_agent_service(tmp_path / "checkpoint.sqlite3", status="normal")
    memory = EquipmentMemoryService(EquipmentMemoryRepository(tmp_path / "memory.sqlite3"))
    workflow.dependencies.memory_service = memory
    manager = AgentRunManager(workflow, tmp_path / "runs.sqlite3", max_workers=1)
    request = AgentRunCreate(equipment_id="fake-rig", measurement_id="fake:measurement:1")
    try:
        run1 = manager.create_run(request)
        manager.wait_for_status(run1.run_id, {"COMPLETED"})
        assert memory.repository.count("fake-rig") == 3

        run2 = manager.create_run(request)
        manager.wait_for_status(run2.run_id, {"COMPLETED"})
        state2 = workflow.get_run(run2.run_id)
        assert state2["memory_used_ids"]
        assert all(item.startswith("memory_") for item in state2["memory_used_ids"])
        assert analysis.calls == 2
        assert state2["analysis_result"]["measurement_id"] == "fake:measurement:1"
    finally:
        manager.close()
