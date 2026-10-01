from datetime import UTC, datetime

from app.memory import EquipmentMemoryRepository, EquipmentMemoryService, MemorySourceType, MemoryStatus, MemoryType


def completed_state(run_id: str = "run-1", *, condition: str = "C1", human: bool = False) -> dict:
    now = datetime.now(UTC).isoformat()
    return {
        "run_id": run_id, "equipment_id": "rig-a", "measurement_id": f"measurement-{run_id}",
        "workflow_status": "COMPLETED", "operating_condition": {"code": condition},
        "measurement_ref": {"measurement_id": f"measurement-{run_id}"},
        "analysis_result": {"analysis_id": f"analysis-{run_id}", "status": "abnormal",
            "predicted_class": "damaged", "model_id": "model-1", "confidence": 0.8,
            "signal_features": {"rms": 1.2, "kurtosis": 3.4}},
        "diagnosis_candidates": [{"candidate_id": "candidate-1", "fault_type": "bearing_condition_anomaly"}],
        "evidence_status": "SUFFICIENT", "inspection_plan": [{"step_id": "step-1"}],
        "recommended_actions": [{"action_id": "action-1"}],
        "human_interactions": [],
        "human_observations": ([{"source": "human", "type": "noise", "value": "observed",
            "recorded_at": now}] if human else []),
        "memory_used_ids": [], "final_report": {"created_at": now},
    }


def test_run_summary_separates_measured_inferred_and_human_memory(tmp_path) -> None:
    service = EquipmentMemoryService(EquipmentMemoryRepository(tmp_path / "memory.sqlite3"))
    records = service.record_run_memory(completed_state(human=True))
    by_type = {item.memory_type: item for item in records}
    assert by_type[MemoryType.ANALYSIS].status == MemoryStatus.MEASURED
    assert by_type[MemoryType.DIAGNOSIS].status == MemoryStatus.INFERRED
    assert by_type[MemoryType.HUMAN_OBSERVATION].source_type == MemorySourceType.HUMAN
    assert not by_type[MemoryType.DIAGNOSIS].structured_data.get("technical_evidence")


def test_first_run_empty_context_is_valid(tmp_path) -> None:
    service = EquipmentMemoryService(EquipmentMemoryRepository(tmp_path / "memory.sqlite3"))
    context = service.get_relevant_context("new-rig")
    assert context.memory_used_ids == []
    assert context.maintenance_history == []


def test_human_observation_is_available_to_a_later_run_context(tmp_path) -> None:
    service = EquipmentMemoryService(EquipmentMemoryRepository(tmp_path / "memory.sqlite3"))
    service.record_run_memory(completed_state("observed-run", human=True))
    later = service.get_relevant_context("rig-a", operating_condition="C1")
    assert len(later.human_observations) == 1
    assert later.human_observations[0].status == MemoryStatus.OBSERVED
    assert later.human_observations[0].structured_data["observation"]["value"] == "observed"
