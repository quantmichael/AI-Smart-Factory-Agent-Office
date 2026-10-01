"""External service boundary for starting and recovering LangGraph runs."""

from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from uuid import uuid4

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from app.agent.graph import build_diagnosis_graph
from app.agent.nodes import AgentDependencies, AgentNodes
from app.domain.schemas import WorkflowStatus
from app.agent.schemas import (
    ApprovalDecision,
    HumanInputResult,
    HumanInputSubmission,
    HumanRequest,
    HumanRequestType,
)


class AgentWorkflowService:
    def __init__(self, dependencies: AgentDependencies, checkpoint_path: Path | str) -> None:
        self.dependencies = dependencies
        self.checkpoint_path = Path(checkpoint_path)
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.checkpoint_path, check_same_thread=False)
        self._checkpointer = SqliteSaver(
            self._connection,
            serde=JsonPlusSerializer(
                pickle_fallback=False,
                allowed_json_modules=None,
                allowed_msgpack_modules=None,
            ),
        )
        self._checkpointer.setup()
        self.graph = build_diagnosis_graph(
            AgentNodes(dependencies), checkpointer=self._checkpointer
        )

    @staticmethod
    def _config(run_id: str) -> dict:
        return {"configurable": {"thread_id": run_id, "checkpoint_ns": ""}}

    def _initial_state(
        self,
        run_id: str,
        measurement_id: str,
        inspection_image_ids: list[str] | None = None,
        demo_scenario: str | None = None,
    ) -> dict:
        return {
            "run_id": run_id,
            "measurement_id": measurement_id,
            "demo_scenario": demo_scenario,
            "workflow_status": WorkflowStatus.CREATED.value,
            "retrieval_retry_count": 0,
            "max_retrieval_retries": self.dependencies.max_retrieval_retries,
            "events": [],
            "node_timings": [],
            "errors": [],
            "retrieval_queries": [],
            "retrieval_records": [],
            "equipment_memory": {},
            "memory_used_ids": [],
            "inspection_image_ids": list(inspection_image_ids or []),
            "visual_observations": [],
            "visual_observation_used_ids": [],
            "version_trace": dict(self.dependencies.version_trace),
            "rag_evidence": [],
            "diagnosis_candidates": [],
            "verification_result": None,
            "additional_information_request": None,
            "human_input": None,
            "final_report": None,
            "next_action": None,
            "inspection_plan": [],
            "recommended_actions": [],
            "pending_human_request": None,
            "human_interactions": [],
            "human_observations": [],
            "human_information_round_count": 0,
            "max_human_information_rounds": self.dependencies.max_human_information_rounds,
            "action_revision_count": 0,
            "max_action_revision_rounds": self.dependencies.max_action_revision_rounds,
        }

    def start_run(
        self,
        measurement_id: str,
        *,
        run_id: str | None = None,
        inspection_image_ids: list[str] | None = None,
        demo_scenario: str | None = None,
    ) -> dict:
        run_id = run_id or f"run_{uuid4().hex}"
        existing = self.get_run(run_id)
        if existing:
            raise ValueError(f"run_id already exists: {run_id}")
        initial = self._initial_state(
            run_id, measurement_id, inspection_image_ids, demo_scenario
        )
        return dict(self.graph.invoke(initial, config=self._config(run_id)))

    def stream_new_run(
        self,
        measurement_id: str,
        *,
        run_id: str,
        inspection_image_ids: list[str] | None = None,
        demo_scenario: str | None = None,
    ):
        """Yield checkpointed state after each graph step for durable event delivery."""

        if self.get_run(run_id):
            raise ValueError(f"run_id already exists: {run_id}")
        yield from self.graph.stream(
            self._initial_state(
                run_id, measurement_id, inspection_image_ids, demo_scenario
            ),
            config=self._config(run_id),
            stream_mode="values",
        )

    def get_run(self, run_id: str) -> dict | None:
        snapshot = self.graph.get_state(self._config(run_id))
        return dict(snapshot.values) if snapshot.values else None

    def resume_run(self, run_id: str) -> dict:
        state = self.get_run(run_id)
        if state is None:
            raise KeyError(f"run not found: {run_id}")
        if state.get("workflow_status") in {
            WorkflowStatus.COMPLETED.value,
            WorkflowStatus.FAILED.value,
            WorkflowStatus.WAITING.value,
        }:
            return state
        return dict(self.graph.invoke(None, config=self._config(run_id)))

    def submit_human_input(
        self, run_id: str, submission: HumanInputSubmission
    ) -> dict:
        self.validate_human_input(run_id, submission)
        result = self.graph.invoke(
            Command(resume=submission.model_dump(mode="json")),
            config=self._config(run_id),
        )
        return dict(result)

    def validate_human_input(
        self, run_id: str, submission: HumanInputSubmission
    ) -> HumanRequest:
        state = self.get_run(run_id)
        if state is None:
            raise KeyError(f"run not found: {run_id}")
        if state.get("workflow_status") != WorkflowStatus.WAITING.value:
            raise ValueError("run is not waiting for human input")
        if not state.get("pending_human_request"):
            raise ValueError("run has no pending human request")
        request = HumanRequest.model_validate(state["pending_human_request"])
        if submission.request_id != request.request_id:
            raise ValueError("request_id does not match the pending request")
        if len(json.dumps(submission.response, ensure_ascii=False)) > 10_000:
            raise ValueError("human response is too large")
        if request.request_type == HumanRequestType.APPROVAL:
            decision = submission.response.get("decision")
            try:
                ApprovalDecision(decision)
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    "approval response decision must be APPROVED, REJECTED, or NEEDS_REVISION"
                ) from exc
        else:
            missing = [
                field
                for field in request.requested_fields
                if field not in submission.response
                or submission.response[field] in (None, "", [], {})
            ]
            if missing:
                raise ValueError(f"human response is missing requested fields: {missing}")
        return request

    def stream_human_input(self, run_id: str, submission: HumanInputSubmission):
        """Resume a validated interrupt and yield state after each graph step."""

        self.validate_human_input(run_id, submission)
        yield from self.graph.stream(
            Command(resume=submission.model_dump(mode="json")),
            config=self._config(run_id),
            stream_mode="values",
        )

    @staticmethod
    def human_input_result(state: dict) -> HumanInputResult:
        return HumanInputResult(
            run_id=state["run_id"],
            workflow_status=state["workflow_status"],
            current_node=state["current_node"],
            next_action=state.get("next_action"),
            pending_human_request=state.get("pending_human_request"),
            final_report=state.get("final_report"),
        )

    def graph_mermaid(self) -> str:
        return self.graph.get_graph().draw_mermaid()

    def close(self) -> None:
        self._connection.close()
