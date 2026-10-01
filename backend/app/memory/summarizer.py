"""Deterministic run-to-memory summaries; no facts are invented here."""

from __future__ import annotations

from typing import Any


def analysis_summary(state: dict[str, Any]) -> str:
    analysis = state["analysis_result"]
    return (
        f"ML analysis classified measurement {state['measurement_id']} as "
        f"{analysis['predicted_class']} ({analysis['status']}) using {analysis['model_id']}."
    )


def diagnosis_summary(state: dict[str, Any]) -> str:
    candidates = state.get("diagnosis_candidates", [])
    if not candidates:
        return "No diagnosis candidate was produced for this run."
    names = ", ".join(item["fault_type"] for item in candidates)
    return (
        f"Agent produced {len(candidates)} inferred diagnosis candidate(s): {names}. "
        "These are not confirmed equipment facts."
    )


def inspection_summary(state: dict[str, Any]) -> str:
    return f"Agent generated {len(state.get('inspection_plan', []))} inspection step(s)."


def action_summary(state: dict[str, Any]) -> str:
    actions = state.get("recommended_actions", [])
    return f"Agent generated {len(actions)} decision-support action recommendation(s)."
