from pathlib import Path

from agent_helpers import build_fake_agent_service


def test_agent_events_are_ordered_unique_and_payloads_are_bounded(tmp_path: Path) -> None:
    service, _, _ = build_fake_agent_service(tmp_path / "checkpoint.sqlite3")
    try:
        state = service.start_run("fake:measurement:1", run_id="event-run")
    finally:
        service.close()

    events = state["events"]
    assert [item["sequence"] for item in events] == list(range(1, len(events) + 1))
    assert len({item["event_id"] for item in events}) == len(events)
    assert events[0]["event_type"] == "workflow_started"
    serialized = str(events).lower()
    assert "raw_signal" not in serialized
    assert "chain-of-thought" not in serialized
    assert "must-not-leak" not in serialized
