#!/usr/bin/env python3
"""Generate sanitized STEP 09 artifacts from real ML and RAG executions."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.agent import build_agent_service  # noqa: E402
from app.agent.actions import ConservativeActionPlanner  # noqa: E402
from app.agent.reasoning import DeterministicEvidenceVerifier  # noqa: E402
from app.agent.schemas import (  # noqa: E402
    ActionPriority,
    ActionType,
    EvidenceStatus,
    HumanInputSubmission,
    VerificationResult,
)


class ShutdownReviewPlanner(ConservativeActionPlanner):
    def recommend_action(self, candidates, evidence, plan):
        base = super().recommend_action(candidates, evidence, plan)[0]
        return [
            base.model_copy(
                update={
                    "action_type": ActionType.SHUTDOWN_CHECK,
                    "priority": ActionPriority.HIGH,
                    "summary": (
                        "Request operator or expert review of whether a controlled stop is needed."
                    ),
                }
            )
        ]


class InsufficientThenDeterministicVerifier:
    def __init__(self) -> None:
        self.calls = 0
        self.delegate = DeterministicEvidenceVerifier()

    def verify(self, candidates, evidence):
        self.calls += 1
        if self.calls == 1:
            return VerificationResult(
                status=EvidenceStatus.INSUFFICIENT,
                missing_information=["inspection observation"],
                summary="Controlled HITL validation requires an inspection observation.",
            )
        return self.delegate.verify(candidates, evidence)


def _service(checkpoint_name: str, **overrides):
    return build_agent_service(
        dataset_root=PROJECT_ROOT / "data/paderborn",
        ml_artifact_root=PROJECT_ROOT / "artifacts/ml",
        active_model_id="bearing_rf_binary_v1",
        vector_db_path=PROJECT_ROOT / "artifacts/vector_db",
        checkpoint_path=PROJECT_ROOT / "artifacts/agent/checkpoints" / checkpoint_name,
        **overrides,
    )


def _compact(state: dict) -> dict:
    return {
        "run_id": state["run_id"],
        "measurement_id": state["measurement_id"],
        "workflow_status": state["workflow_status"],
        "current_node": state["current_node"],
        "next_action": state.get("next_action"),
        "analysis_result": {
            key: state["analysis_result"].get(key)
            for key in (
                "analysis_id",
                "model_id",
                "status",
                "predicted_class",
                "confidence",
                "signal_features",
            )
        },
        "evidence_status": state.get("evidence_status"),
        "evidence": [
            {
                key: item.get(key)
                for key in (
                    "evidence_id",
                    "query_id",
                    "purpose",
                    "document_id",
                    "chunk_id",
                    "source_id",
                    "title",
                    "publisher",
                    "source_tier",
                    "page",
                    "section",
                    "retrieval_score",
                    "official_url",
                )
            }
            for item in state.get("rag_evidence", [])
        ],
        "diagnosis_candidates": state.get("diagnosis_candidates", []),
        "inspection_plan": state.get("inspection_plan", []),
        "recommended_actions": state.get("recommended_actions", []),
        "pending_human_request": state.get("pending_human_request"),
        "human_interactions": state.get("human_interactions", []),
        "human_observations": state.get("human_observations", []),
        "human_information_round_count": state.get("human_information_round_count"),
        "action_revision_count": state.get("action_revision_count"),
        "final_report": state.get("final_report"),
        "events": state.get("events", []),
        "errors": state.get("errors", []),
    }


def main() -> int:
    artifact_root = PROJECT_ROOT / "artifacts/agent/actions_hitl"
    artifact_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    measurement = "paderborn:KA01:N09_M07_F10:01"

    sufficient_service = _service("actions_hitl_sufficient.sqlite3")
    try:
        sufficient = sufficient_service.start_run(
            measurement, run_id=f"run_step09_sufficient_{stamp}"
        )
    finally:
        sufficient_service.close()

    approval_service = _service(
        "actions_hitl_approval.sqlite3", action_planner=ShutdownReviewPlanner()
    )
    try:
        approval_waiting = approval_service.start_run(
            measurement, run_id=f"run_step09_approval_{stamp}"
        )
        approval_request = approval_waiting["pending_human_request"]
        approval = approval_service.submit_human_input(
            approval_waiting["run_id"],
            HumanInputSubmission(
                request_id=approval_request["request_id"],
                response={"decision": "APPROVED"},
                comment="Controlled STEP 09 validation approval; not a factual diagnosis label.",
            ),
        )
    finally:
        approval_service.close()

    information_service = _service(
        "actions_hitl_information.sqlite3",
        evidence_verifier=InsufficientThenDeterministicVerifier(),
    )
    try:
        information_waiting = information_service.start_run(
            measurement, run_id=f"run_step09_information_{stamp}"
        )
        information_request = information_waiting["pending_human_request"]
        information = information_service.submit_human_input(
            information_waiting["run_id"],
            HumanInputSubmission(
                request_id=information_request["request_id"],
                response={
                    "inspection_observation": (
                        "Controlled validation observation: abnormal noise noted; no visible leakage."
                    ),
                    "operating_condition_confirmation": "N09_M07_F10 confirmed.",
                },
                comment="Controlled input used only to validate checkpoint resume and re-retrieval.",
            ),
        )
    finally:
        information_service.close()

    outputs = {
        "sufficient_run.json": _compact(sufficient),
        "human_approval_run.json": {
            "waiting_checkpoint": _compact(approval_waiting),
            "resumed_result": _compact(approval),
        },
        "human_information_run.json": {
            "waiting_checkpoint": _compact(information_waiting),
            "resumed_result": _compact(information),
        },
        "final_report_sample.json": sufficient["final_report"],
    }
    for name, payload in outputs.items():
        (artifact_root / name).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    report = [
        "# Agent Actions and HITL Report",
        "",
        "## Sufficient flow",
        "",
        f"- Run: `{sufficient['run_id']}`",
        f"- Evidence: {len(sufficient['rag_evidence'])}",
        f"- Inspection steps: {len(sufficient['inspection_plan'])}",
        f"- Actions: {len(sufficient['recommended_actions'])}",
        f"- Result: `{sufficient['workflow_status']}/{sufficient['next_action']}`",
        "",
        "## Approval flow",
        "",
        f"- Run: `{approval['run_id']}`",
        f"- Wait state: `{approval_waiting['workflow_status']}`",
        f"- Request: `{approval_request['request_id']}`",
        "- Decision: `APPROVED`",
        f"- Result: `{approval['workflow_status']}/{approval['next_action']}`",
        "",
        "## Additional-information flow",
        "",
        f"- Run: `{information['run_id']}`",
        f"- Wait state: `{information_waiting['workflow_status']}`",
        f"- Request: `{information_request['request_id']}`",
        f"- Human observations: {len(information['human_observations'])}",
        f"- Result: `{information['workflow_status']}/{information['next_action']}`",
        "",
        "## Safety",
        "",
        "- Recommendations do not execute equipment control.",
        "- SHUTDOWN_CHECK is an operator/expert review request, not a shutdown command.",
        "- Human approval records workflow review and does not validate the diagnosis as fact.",
        "- Report citations are generated only from retrieved EvidenceObject metadata.",
        "- Sanitized artifacts omit source content, raw signals, secrets, and private reasoning.",
        "",
    ]
    (artifact_root / "ACTIONS_HITL_REPORT.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "sufficient": {
                    "run_id": sufficient["run_id"],
                    "inspection_steps": len(sufficient["inspection_plan"]),
                    "actions": len(sufficient["recommended_actions"]),
                    "citations": len(sufficient["final_report"]["citations"]),
                },
                "approval": {
                    "run_id": approval["run_id"],
                    "waited": approval_waiting["workflow_status"] == "WAITING",
                    "decision": approval["human_interactions"][-1]["response"]["decision"],
                },
                "additional_information": {
                    "run_id": information["run_id"],
                    "waited": information_waiting["workflow_status"] == "WAITING",
                    "human_observations": len(information["human_observations"]),
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
