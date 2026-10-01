"""Controlled real-data HITL app used only for STEP 11 browser E2E capture."""

from app.agent.actions import ConservativeActionPlanner
from app.agent.factory import build_agent_service
from app.agent.run_manager import AgentRunManager
from app.agent.schemas import ActionPriority, ActionType
from app.api.v1.agent import get_agent_run_manager
from app.core.config import get_settings
from app.main import app


class ControlledReviewPlanner(ConservativeActionPlanner):
    def recommend_action(self, candidates, evidence, plan):
        base = super().recommend_action(candidates, evidence, plan)[0]
        return [
            base.model_copy(
                update={
                    "action_type": ActionType.SHUTDOWN_CHECK,
                    "priority": ActionPriority.HIGH,
                    "summary": "Request operator review of whether a controlled stop is needed.",
                }
            )
        ]


settings = get_settings()
workflow = build_agent_service(
    dataset_root=settings.paderborn_data_root,
    ml_artifact_root=settings.ml_artifact_root,
    active_model_id=settings.active_ml_model_id,
    vector_db_path=settings.vector_db_path,
    checkpoint_path="../artifacts/api/runtime/step11_hitl_checkpoint.sqlite3",
    max_retrieval_retries=settings.max_retrieval_retries,
    max_human_information_rounds=settings.max_human_information_rounds,
    max_action_revision_rounds=settings.max_action_revision_rounds,
    action_planner=ControlledReviewPlanner(),
)
manager = AgentRunManager(
    workflow,
    "../artifacts/api/runtime/step11_hitl_runs.sqlite3",
    max_workers=2,
)


def get_controlled_manager() -> AgentRunManager:
    return manager


app.dependency_overrides[get_agent_run_manager] = get_controlled_manager
