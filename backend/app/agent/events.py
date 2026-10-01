"""Idempotent AgentEvent creation with run-local ordering."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from app.domain.schemas import AgentEvent


ROLE_BY_NODE = {
    "initialize_run": "SYSTEM",
    "load_sensor_data": "SENSOR_AGENT",
    "load_equipment_memory": "SYSTEM",
    "run_detection": "DETECTION_AGENT",
    "check_abnormal": "DETECTION_AGENT",
    "check_inspection_image": "DIAGNOSIS_AGENT",
    "analyze_inspection_image": "DIAGNOSIS_AGENT",
    "merge_visual_context": "DIAGNOSIS_AGENT",
    "save_normal_state": "DETECTION_AGENT",
    "generate_normal_report": "DETECTION_AGENT",
    "build_rag_query": "RAG_AGENT",
    "retrieve_knowledge": "RAG_AGENT",
    "refine_query": "RAG_AGENT",
    "retrieve_counter_evidence": "RAG_AGENT",
    "diagnose": "DIAGNOSIS_AGENT",
    "verify_evidence": "DIAGNOSIS_AGENT",
    "ready_for_inspection": "DIAGNOSIS_AGENT",
    "needs_additional_information": "DIAGNOSIS_AGENT",
    "build_inspection_plan": "MAINTENANCE_AGENT",
    "recommend_action": "MAINTENANCE_AGENT",
    "check_human_approval": "MAINTENANCE_AGENT",
    "request_human_approval": "MAINTENANCE_AGENT",
    "request_additional_information": "DIAGNOSIS_AGENT",
    "await_human_input": "DIAGNOSIS_AGENT",
    "resume_after_human": "DIAGNOSIS_AGENT",
    "update_context": "DIAGNOSIS_AGENT",
    "generate_report": "MAINTENANCE_AGENT",
}


def make_events(
    state: dict[str, Any],
    node: str,
    message: str,
    *,
    payload: dict[str, Any] | None = None,
    workflow_started: bool = False,
    extra_events: list[tuple[str, str]] | None = None,
) -> list[dict[str, Any]]:
    run_id = state["run_id"]
    existing = state.get("events", [])
    sequence = len(existing) + 1
    specs = []
    if workflow_started:
        specs.append(("workflow_started", "Workflow started."))
    specs.extend((("node_started", f"{node} started."), ("node_completed", message)))
    specs.extend(extra_events or [])
    events = []
    for offset, (event_type, event_message) in enumerate(specs):
        attempt = ":".join(
            str(value)
            for value in (
                state.get("retrieval_retry_count", 0),
                state.get("human_information_round_count", 0),
                state.get("action_revision_count", 0),
                len(state.get("human_interactions", [])),
            )
        )
        identity = f"{run_id}:{node}:{event_type}:{attempt}"
        event = AgentEvent(
            event_id="event_" + hashlib.sha256(identity.encode()).hexdigest()[:20],
            run_id=run_id,
            sequence=sequence + offset,
            event_type=event_type,
            node=node,
            agent_role=ROLE_BY_NODE[node],
            message=event_message,
            payload=payload or {},
            created_at=datetime.now(UTC),
        )
        events.append(event.model_dump(mode="json"))
    return events


def make_error_event(
    state: dict[str, Any], node: str, error_type: str
) -> dict[str, Any]:
    sequence = len(state.get("events", [])) + 1
    identity = (
        f"{state['run_id']}:{node}:workflow_error:{error_type}:"
        f"{state.get('retrieval_retry_count', 0)}:"
        f"{state.get('human_information_round_count', 0)}:"
        f"{state.get('action_revision_count', 0)}"
    )
    return AgentEvent(
        event_id="event_" + hashlib.sha256(identity.encode()).hexdigest()[:20],
        run_id=state["run_id"],
        sequence=sequence,
        event_type="workflow_error",
        node=node,
        agent_role=ROLE_BY_NODE.get(node, "SYSTEM"),
        message=f"Workflow stopped because {error_type} occurred.",
        payload={"error_type": error_type},
        created_at=datetime.now(UTC),
    ).model_dump(mode="json")
