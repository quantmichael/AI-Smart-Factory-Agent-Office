from pathlib import Path

from app.agent.schemas import HumanInputSubmission
from agent_helpers import ShutdownReviewPlanner, build_fake_agent_service


def test_needs_revision_returns_to_recommendation_with_bounded_rounds(tmp_path: Path) -> None:
    service, _, _ = build_fake_agent_service(
        tmp_path / "checkpoint.sqlite3",
        planner=ShutdownReviewPlanner(),
        max_revision_rounds=1,
    )
    first = service.start_run("fake:measurement:1", run_id="revision-run")
    second = service.submit_human_input(
        first["run_id"],
        HumanInputSubmission(
            request_id=first["pending_human_request"]["request_id"],
            response={"decision": "NEEDS_REVISION"},
            comment="Clarify operator review.",
        ),
    )
    assert second["workflow_status"] == "WAITING"
    assert second["action_revision_count"] == 1
    final = service.submit_human_input(
        second["run_id"],
        HumanInputSubmission(
            request_id=second["pending_human_request"]["request_id"],
            response={"decision": "REJECTED"},
        ),
    )
    service.close()

    assert final["workflow_status"] == "COMPLETED"
    assert len(final["human_interactions"]) == 2
