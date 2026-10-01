"""Deterministic safety and approval rules for recommendations."""

from __future__ import annotations

from app.agent.schemas import ActionPriority, ActionType, RecommendedAction


class ActionPolicy:
    allowed_actions = frozenset(ActionType)
    prohibited_phrases = (
        "automatically shut down",
        "direct plc",
        "bypass interlock",
        "automatically execute maintenance",
    )

    def apply(
        self, action: RecommendedAction, *, valid_evidence_ids: set[str]
    ) -> RecommendedAction:
        if action.action_type not in self.allowed_actions:
            raise ValueError(f"action type is not allowed: {action.action_type}")
        unknown = set(action.supporting_evidence_ids) - valid_evidence_ids
        if unknown:
            raise ValueError(f"action references unknown evidence IDs: {sorted(unknown)}")
        text = f"{action.summary} {action.reason}".lower()
        if any(phrase in text for phrase in self.prohibited_phrases):
            raise ValueError("recommended action violates the no-automatic-control guardrail")
        important = action.action_type in {
            ActionType.SHUTDOWN_CHECK,
            ActionType.SCHEDULE_MAINTENANCE,
        } or action.priority == ActionPriority.HIGH
        if important and not action.supporting_evidence_ids:
            raise ValueError("important actions require supporting evidence")
        limitations = list(action.limitations)
        if action.action_type == ActionType.SHUTDOWN_CHECK:
            limitations.append(
                "SHUTDOWN_CHECK requests operator/expert review and is not a shutdown command."
            )
        return action.model_copy(
            update={
                "requires_human_approval": important,
                "limitations": list(dict.fromkeys(limitations)),
            }
        )
