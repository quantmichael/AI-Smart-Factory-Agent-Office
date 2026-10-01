"""Pure deterministic routing functions used by the LangGraph edges."""

from app.agent.schemas import EvidenceStatus
from app.agent.state import AgentState


def route_if_failed(state: AgentState) -> str:
    return "failed" if state.get("workflow_status") == "FAILED" else "continue"


def route_analysis(state: AgentState) -> str:
    status = state["analysis_result"]["status"]
    if status == "normal":
        return "normal"
    if status == "abnormal":
        return "abnormal"
    raise ValueError(f"unsupported analysis status: {status}")


def route_inspection_image(state: AgentState) -> str:
    return "image" if state.get("inspection_image_ids") else "no_image"


def route_evidence(state: AgentState) -> str:
    status = EvidenceStatus(state["evidence_status"])
    retries = state.get("retrieval_retry_count", 0)
    maximum = state.get("max_retrieval_retries", 2)
    if status == EvidenceStatus.SUFFICIENT:
        return "sufficient"
    if status == EvidenceStatus.INSUFFICIENT:
        return (
            "limited_report"
            if state.get("human_information_round_count", 0)
            >= state.get("max_human_information_rounds", 2)
            else "additional_information"
        )
    if retries >= maximum:
        return (
            "limited_report"
            if state.get("human_information_round_count", 0)
            >= state.get("max_human_information_rounds", 2)
            else "additional_information"
        )
    if status == EvidenceStatus.PARTIAL:
        return "refine"
    return "counter_evidence"


def route_human_approval(state: AgentState) -> str:
    return (
        "approval"
        if any(
            item.get("requires_human_approval")
            for item in state.get("recommended_actions", [])
        )
        else "report"
    )


def route_human_response(state: AgentState) -> str:
    interaction = state["human_interactions"][-1]
    if interaction["request_type"] == "ADDITIONAL_INFORMATION":
        return "update_context"
    decision = interaction["response"]["decision"]
    if decision == "NEEDS_REVISION" and state.get("action_revision_count", 0) <= state.get(
        "max_action_revision_rounds", 1
    ):
        return "revise"
    return "report"
