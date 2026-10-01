"""Generate STEP 10 API/SSE evidence from real local measurements."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.agent.actions import ConservativeActionPlanner
from app.agent.factory import build_agent_service
from app.agent.run_manager import AgentRunManager
from app.agent.schemas import ActionPriority, ActionType
from app.api.v1.agent import get_agent_run_manager
from app.core.config import Settings
from app.main import app


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "artifacts/api/agent_sse"
RUNTIME = ROOT / "artifacts/api/runtime"
EQUIPMENT_ID = "paderborn-bearing-test-rig"
NORMAL_ID = "paderborn:K001:N09_M07_F10:01"
ABNORMAL_ID = "paderborn:KA01:N09_M07_F10:01"


class ShutdownReviewPlanner(ConservativeActionPlanner):
    """Controlled HITL scenario; policy still prevents automatic control."""

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


def manager(settings: Settings, name: str, *, hitl: bool = False) -> AgentRunManager:
    workflow = build_agent_service(
        dataset_root=ROOT / "data/paderborn",
        ml_artifact_root=ROOT / "artifacts/ml",
        active_model_id=settings.active_ml_model_id,
        vector_db_path=ROOT / "artifacts/vector_db",
        checkpoint_path=RUNTIME / f"{name}_checkpoint.sqlite3",
        max_retrieval_retries=settings.max_retrieval_retries,
        max_human_information_rounds=settings.max_human_information_rounds,
        max_action_revision_rounds=settings.max_action_revision_rounds,
        action_planner=ShutdownReviewPlanner() if hitl else None,
    )
    return AgentRunManager(workflow, RUNTIME / "agent_runs.sqlite3")


def stream_events(client: TestClient, run_id: str) -> list[dict]:
    response = client.get(f"/api/v1/agent/runs/{run_id}/events/stream")
    response.raise_for_status()
    return [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]


def execute(
    client: TestClient,
    run_manager: AgentRunManager,
    measurement_id: str,
    *,
    hitl: bool = False,
) -> tuple[dict, list[dict]]:
    response = client.post(
        "/api/v1/agent/runs",
        json={"equipment_id": EQUIPMENT_ID, "measurement_id": measurement_id},
    )
    response.raise_for_status()
    run_id = response.json()["run_id"]
    target = {"WAITING"} if hitl else {"COMPLETED", "FAILED", "WAITING"}
    run = run_manager.wait_for_status(run_id, target, timeout_seconds=30)
    if hitl:
        human = client.post(
            f"/api/v1/agent/runs/{run_id}/human-input",
            json={
                "request_id": run.pending_human_request.request_id,
                "response": {"decision": "APPROVED"},
                "comment": "STEP 10 controlled API verification.",
                "actor": "step10-e2e",
            },
        )
        human.raise_for_status()
        run = run_manager.wait_for_status(run_id, {"COMPLETED", "FAILED"}, timeout_seconds=30)
    if run.workflow_status.value != "COMPLETED":
        raise RuntimeError(f"run {run_id} ended in {run.workflow_status.value}")
    state = client.get(f"/api/v1/agent/runs/{run_id}")
    state.raise_for_status()
    report = client.get(f"/api/v1/agent/runs/{run_id}/report")
    report.raise_for_status()
    return {"run": state.json(), "report": report.json()}, stream_events(client, run_id)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    settings = Settings()
    client = TestClient(app)
    results = {}
    for name, measurement_id, hitl in (
        ("normal", NORMAL_ID, False),
        ("abnormal", ABNORMAL_ID, False),
        ("hitl", ABNORMAL_ID, True),
    ):
        run_manager = manager(settings, name, hitl=hitl)
        def override_manager() -> AgentRunManager:
            return run_manager

        app.dependency_overrides[get_agent_run_manager] = override_manager
        try:
            result, events = execute(client, run_manager, measurement_id, hitl=hitl)
            (OUTPUT / f"{name}_event_stream.json").write_text(
                json.dumps(events, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            results[name] = {
                **result,
                "event_count": len(events),
                "event_types": [event["event_type"] for event in events],
            }
        finally:
            app.dependency_overrides.clear()
            run_manager.close()

    generated = datetime.now(UTC).isoformat()
    report = f"""# STEP 10 Agent API & SSE Report

- Generated: `{generated}`
- Execution: real local Paderborn measurements through FastAPI, LangGraph, ML, RAG, and SSE
- Reconnect contract: `after_sequence` query parameter
- WAITING policy: deliver persisted events, then close; reconnect after human input
- Heartbeat: SSE comment, not persisted

## Event → UI State Mapping

| Event | UI state update |
|---|---|
| `node_started` | Mark the mapped `agent_role` as working |
| `detection_normal` / `detection_abnormal` | Update analysis summary and detection state |
| `retrieval_completed` | Update RAG evidence count |
| `evidence_status_changed` | Update evidence status and retry count |
| `human_input_required` | Set workflow to WAITING and show the pending request |
| `human_input_received` / `workflow_resumed` | Clear the modal and resume the same run |
| `report_generated` | Mark the report as available |
| `workflow_completed` | Mark all applicable work complete |
| `workflow_error` | Show the persisted workflow error state |

## Verified Runs

| Scenario | Run ID | Events | Status | Evidence | Report |
|---|---|---:|---|---:|---|
| Normal | `{results['normal']['run']['run_id']}` | {results['normal']['event_count']} | {results['normal']['run']['workflow_status']} | {results['normal']['run']['evidence_count']} | ready |
| Abnormal | `{results['abnormal']['run']['run_id']}` | {results['abnormal']['event_count']} | {results['abnormal']['run']['workflow_status']} | {results['abnormal']['run']['evidence_count']} | ready |
| HITL | `{results['hitl']['run']['run_id']}` | {results['hitl']['event_count']} | {results['hitl']['run']['workflow_status']} | {results['hitl']['run']['evidence_count']} | ready |

No timer-generated or replayed progress is used. The event files are parsed from the actual SSE responses.
"""
    (OUTPUT / "AGENT_API_SSE_REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
