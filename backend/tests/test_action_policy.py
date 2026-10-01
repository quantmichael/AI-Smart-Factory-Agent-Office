import pytest

from app.agent.policies import ActionPolicy
from app.agent.schemas import ActionPriority, ActionType, RecommendedAction


def _action(**updates) -> RecommendedAction:
    values = {
        "action_id": "action-1",
        "action_type": ActionType.INSPECT,
        "priority": ActionPriority.MEDIUM,
        "summary": "Perform evidence-linked inspection.",
        "reason": "Technical evidence supports inspection.",
        "supporting_evidence_ids": ["evidence-1"],
    }
    values.update(updates)
    return RecommendedAction(**values)


def test_action_policy_requires_approval_for_important_actions() -> None:
    policy = ActionPolicy()
    inspect = policy.apply(_action(), valid_evidence_ids={"evidence-1"})
    shutdown_review = policy.apply(
        _action(
            action_type=ActionType.SHUTDOWN_CHECK,
            priority=ActionPriority.HIGH,
            summary="Request an operator review of whether stopping is appropriate.",
        ),
        valid_evidence_ids={"evidence-1"},
    )

    assert inspect.requires_human_approval is False
    assert shutdown_review.requires_human_approval is True
    assert any("not a shutdown command" in item for item in shutdown_review.limitations)


def test_action_policy_rejects_fake_evidence_and_automatic_control_language() -> None:
    policy = ActionPolicy()
    with pytest.raises(ValueError, match="unknown evidence"):
        policy.apply(_action(), valid_evidence_ids=set())
    with pytest.raises(ValueError, match="no-automatic-control"):
        policy.apply(
            _action(summary="Automatically shut down the machine."),
            valid_evidence_ids={"evidence-1"},
        )
