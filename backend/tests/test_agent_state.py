from app.agent.state import AgentState, merge_events


def test_agent_state_contract_excludes_raw_signal_arrays() -> None:
    assert "raw_signal" not in AgentState.__annotations__
    assert "raw_signals" not in AgentState.__annotations__
    assert {"measurement_id", "analysis_result", "rag_evidence", "workflow_status"} <= set(
        AgentState.__annotations__
    )


def test_event_reducer_is_idempotent_and_sequence_ordered() -> None:
    event1 = {"event_id": "a", "sequence": 1}
    event2 = {"event_id": "b", "sequence": 2}
    assert merge_events([event1], [event2, event1]) == [event1, event2]
