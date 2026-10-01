from pathlib import Path

import pytest

from app.agent import build_agent_service
from app.agent.schemas import HumanInputSubmission


@pytest.mark.integration
def test_real_normal_and_abnormal_measurements_follow_distinct_graph_paths(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    service = build_agent_service(
        dataset_root=root / "data/paderborn",
        ml_artifact_root=root / "artifacts/ml",
        active_model_id="bearing_rf_binary_v1",
        vector_db_path=root / "artifacts/vector_db",
        checkpoint_path=tmp_path / "checkpoint.sqlite3",
    )
    try:
        normal = service.start_run(
            "paderborn:K001:N09_M07_F10:01", run_id="real-normal"
        )
        abnormal = service.start_run(
            "paderborn:KA01:N09_M07_F10:01", run_id="real-abnormal"
        )
    finally:
        service.close()

    assert normal["analysis_result"]["status"] == "normal"
    assert normal["rag_evidence"] == []
    assert normal["workflow_status"] == "COMPLETED"
    assert abnormal["analysis_result"]["status"] == "abnormal"
    assert abnormal["rag_evidence"]
    assert abnormal["diagnosis_candidates"]
    assert abnormal["evidence_status"] == "SUFFICIENT"
    assert abnormal["next_action"] == "REPORT_COMPLETE"
    assert abnormal["inspection_plan"]
    assert abnormal["recommended_actions"]
    assert abnormal["final_report"]["citations"]
    assert all(
        item["source_id"] not in {
            "PADERBORN_DAMAGE_FACT_SHEETS",
            "PADERBORN_MEASUREMENT_LOGS",
        }
        for item in abnormal["rag_evidence"]
    )


@pytest.mark.integration
def test_real_controlled_hitl_measurement_waits_and_resumes_same_run(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    service = build_agent_service(
        dataset_root=root / "data/paderborn",
        ml_artifact_root=root / "artifacts/ml",
        active_model_id="bearing_rf_binary_v1",
        vector_db_path=root / "artifacts/vector_db",
        checkpoint_path=tmp_path / "checkpoint.sqlite3",
    )
    try:
        waiting = service.start_run(
            "paderborn:KA01:N09_M07_F10:02",
            run_id="real-controlled-hitl",
            demo_scenario="HITL_CONTROLLED",
        )
        request = waiting["pending_human_request"]
        completed = service.submit_human_input(
            waiting["run_id"],
            HumanInputSubmission(
                request_id=request["request_id"],
                response={"decision": "APPROVED"},
                comment="Controlled E2E approval.",
                actor="test-operator",
            ),
        )
    finally:
        service.close()

    assert waiting["analysis_result"]["status"] == "abnormal"
    assert waiting["workflow_status"] == "WAITING"
    assert waiting["demo_scenario"] == "HITL_CONTROLLED"
    assert waiting["rag_evidence"]
    assert request["request_type"] == "APPROVAL"
    assert waiting["recommended_actions"][0]["action_type"] == "SHUTDOWN_CHECK"
    assert waiting["recommended_actions"][0]["requires_human_approval"] is True
    assert completed["run_id"] == waiting["run_id"]
    assert completed["workflow_status"] == "COMPLETED"
    assert completed["final_report"] is not None
    assert len(completed["human_interactions"]) == 1
