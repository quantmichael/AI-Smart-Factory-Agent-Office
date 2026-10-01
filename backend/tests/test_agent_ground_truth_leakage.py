from pathlib import Path

from agent_helpers import build_fake_agent_service


def test_diagnostic_graph_state_and_queries_exclude_ground_truth_fields(tmp_path: Path) -> None:
    service, _, _ = build_fake_agent_service(tmp_path / "checkpoint.sqlite3")
    try:
        state = service.start_run("fake:measurement:1", run_id="leakage-run")
    finally:
        service.close()

    serialized_queries = str(state["retrieval_queries"])
    assert "must-not-leak" not in str(state)
    assert "KA01" not in serialized_queries
    assert "PADERBORN_DAMAGE_FACT_SHEETS" not in serialized_queries
    assert "PADERBORN_MEASUREMENT_LOGS" not in serialized_queries
