import json

from fastapi.testclient import TestClient

from app.agent.schemas import AgentRunCreate
from app.api.v1.agent import get_agent_run_manager
from app.main import app
from api_helpers import build_fake_run_manager


def _parse_sse(body: str) -> list[dict]:
    return [
        json.loads(line.removeprefix("data: "))
        for line in body.splitlines()
        if line.startswith("data: ")
    ]


def test_sse_orders_events_and_reconnects_after_sequence(tmp_path):
    manager = build_fake_run_manager(tmp_path, status="normal")
    created = manager.create_run(
        AgentRunCreate(equipment_id="fake-rig", measurement_id="fake:measurement:1")
    )
    manager.wait_for_status(created.run_id, {"COMPLETED"})
    app.dependency_overrides[get_agent_run_manager] = lambda: manager
    client = TestClient(app)
    try:
        full = client.get(f"/api/v1/agent/runs/{created.run_id}/events/stream")
        all_events = _parse_sse(full.text)
        reconnect = client.get(
            f"/api/v1/agent/runs/{created.run_id}/events/stream",
            params={"after_sequence": all_events[3]["sequence"]},
        )
        later_events = _parse_sse(reconnect.text)
    finally:
        app.dependency_overrides.clear()
        manager.close()

    assert full.headers["content-type"].startswith("text/event-stream")
    assert [item["sequence"] for item in all_events] == list(
        range(1, len(all_events) + 1)
    )
    assert len({item["event_id"] for item in all_events}) == len(all_events)
    assert all(item["run_id"] == created.run_id for item in all_events)
    assert all(item["sequence"] > all_events[3]["sequence"] for item in later_events)
    assert all_events[-1]["event_type"] == "workflow_completed"


def test_event_persistence_is_isolated_by_run(tmp_path):
    manager = build_fake_run_manager(tmp_path, status="normal")
    first = manager.create_run(
        AgentRunCreate(equipment_id="fake-rig", measurement_id="fake:measurement:1")
    )
    second = manager.create_run(
        AgentRunCreate(equipment_id="fake-rig", measurement_id="fake:measurement:1")
    )
    manager.wait_for_status(first.run_id, {"COMPLETED"})
    manager.wait_for_status(second.run_id, {"COMPLETED"})
    first_events = manager.get_events(first.run_id)
    second_events = manager.get_events(second.run_id)
    manager.close()

    assert first_events and second_events
    assert {item.run_id for item in first_events} == {first.run_id}
    assert {item.run_id for item in second_events} == {second.run_id}
    assert not ({item.event_id for item in first_events} & {item.event_id for item in second_events})
