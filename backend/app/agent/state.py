"""Serializable LangGraph state; raw signal arrays are intentionally excluded."""

from __future__ import annotations

from typing import Annotated, Any, TypedDict


def merge_events(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Append events idempotently while preserving their run-local sequence."""

    merged = {item["event_id"]: item for item in [*left, *right]}
    return sorted(merged.values(), key=lambda item: item["sequence"])


def append_records(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [*left, *right]


class AgentState(TypedDict, total=False):
    run_id: str
    equipment_id: str
    measurement_id: str
    demo_scenario: str | None
    measurement_ref: dict[str, Any]
    operating_condition: dict[str, Any]
    equipment_memory: dict[str, Any]
    memory_used_ids: list[str]
    inspection_image_ids: list[str]
    visual_observations: list[dict[str, Any]]
    visual_observation_used_ids: list[str]
    analysis_result: dict[str, Any]
    pending_queries: list[dict[str, Any]]
    retrieval_queries: list[dict[str, Any]]
    retrieval_records: list[dict[str, Any]]
    rag_evidence: list[dict[str, Any]]
    diagnosis_candidates: list[dict[str, Any]]
    verification_result: dict[str, Any] | None
    evidence_status: str | None
    retrieval_retry_count: int
    max_retrieval_retries: int
    additional_information_request: dict[str, Any] | None
    human_input: dict[str, Any] | None
    inspection_plan: list[dict[str, Any]]
    recommended_actions: list[dict[str, Any]]
    pending_human_request: dict[str, Any] | None
    human_interactions: list[dict[str, Any]]
    human_observations: list[dict[str, Any]]
    human_information_round_count: int
    max_human_information_rounds: int
    action_revision_count: int
    max_action_revision_rounds: int
    current_node: str
    workflow_status: str
    next_action: str | None
    final_report: dict[str, Any] | None
    errors: list[dict[str, Any]]
    events: Annotated[list[dict[str, Any]], merge_events]
    node_timings: Annotated[list[dict[str, Any]], append_records]
    reasoning_provider: str
    version_trace: dict[str, str]
