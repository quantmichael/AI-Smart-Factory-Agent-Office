#!/usr/bin/env python3
"""Run real STEP 08 normal/abnormal scenarios and write sanitized artifacts."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.agent import build_agent_service  # noqa: E402
from app.agent.routing import route_analysis, route_evidence  # noqa: E402


def _compact(state: dict) -> dict:
    analysis = state.get("analysis_result") or {}
    return {
        "run_id": state["run_id"],
        "measurement_id": state["measurement_id"],
        "workflow_status": state["workflow_status"],
        "current_node": state["current_node"],
        "next_action": state.get("next_action"),
        "analysis_result": {
            key: analysis.get(key)
            for key in (
                "analysis_id",
                "measurement_id",
                "model_id",
                "status",
                "predicted_class",
                "confidence",
                "signal_features",
            )
        },
        "retrieval_queries": state.get("retrieval_queries", []),
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
        "verification_result": state.get("verification_result"),
        "evidence_status": state.get("evidence_status"),
        "retrieval_retry_count": state.get("retrieval_retry_count"),
        "max_retrieval_retries": state.get("max_retrieval_retries"),
        "reasoning_provider": state.get("reasoning_provider"),
        "events": state.get("events", []),
        "node_timings": state.get("node_timings", []),
        "errors": state.get("errors", []),
        "final_report": state.get("final_report"),
    }


def main() -> int:
    artifact_root = PROJECT_ROOT / "artifacts/agent/langgraph_core"
    artifact_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    service = build_agent_service(
        dataset_root=PROJECT_ROOT / "data/paderborn",
        ml_artifact_root=PROJECT_ROOT / "artifacts/ml",
        active_model_id="bearing_rf_binary_v1",
        vector_db_path=PROJECT_ROOT / "artifacts/vector_db",
        checkpoint_path=PROJECT_ROOT
        / "artifacts/agent/checkpoints/langgraph_core.sqlite3",
        max_retrieval_retries=2,
    )
    try:
        normal = service.start_run(
            "paderborn:K001:N09_M07_F10:01",
            run_id=f"run_step08_normal_{stamp}",
        )
        abnormal = service.start_run(
            "paderborn:KA01:N09_M07_F10:01",
            run_id=f"run_step08_abnormal_{stamp}",
        )
        mermaid = service.graph_mermaid()
        reloaded = service.get_run(abnormal["run_id"])
        assert reloaded and reloaded["events"] == abnormal["events"]
    finally:
        service.close()

    normal_compact, abnormal_compact = _compact(normal), _compact(abnormal)
    routing = {
        "normal": route_analysis({"analysis_result": {"status": "normal"}}),
        "abnormal": route_analysis({"analysis_result": {"status": "abnormal"}}),
        "evidence_routes": {
            status: route_evidence(
                {
                    "evidence_status": status,
                    "retrieval_retry_count": 0,
                    "max_retrieval_retries": 2,
                }
            )
            for status in ("SUFFICIENT", "PARTIAL", "INSUFFICIENT", "CONFLICTING")
        },
        "partial_at_retry_limit": route_evidence(
            {
                "evidence_status": "PARTIAL",
                "retrieval_retry_count": 2,
                "max_retrieval_retries": 2,
            }
        ),
        "conflicting_at_retry_limit": route_evidence(
            {
                "evidence_status": "CONFLICTING",
                "retrieval_retry_count": 2,
                "max_retrieval_retries": 2,
            }
        ),
        "max_retrieval_retries": 2,
        "checkpoint_reload_verified": True,
    }
    (artifact_root / "graph.mmd").write_text(mermaid, encoding="utf-8")
    for name, payload in (
        ("normal_run.json", normal_compact),
        ("abnormal_run.json", abnormal_compact),
        ("routing_test_report.json", routing),
    ):
        (artifact_root / name).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    report = [
        "# LangGraph Core Report",
        "",
        "- Graph: actual LangGraph `StateGraph`",
        "- Checkpoint: SQLite (`SqliteSaver`, strict serializer allowlist)",
        "- Max workflow retrieval retries: 2",
        "- Reasoning provider: `deterministic-evidence-grounded-v1`",
        "",
        "## Normal E2E",
        "",
        f"- Measurement: `{normal['measurement_id']}`",
        f"- ML status: `{normal['analysis_result']['status']}`",
        f"- RAG called: `{bool(normal['retrieval_records'])}`",
        f"- Result: `{normal['workflow_status']}/{normal['next_action']}`",
        f"- Events: {len(normal['events'])}",
        "",
        "## Abnormal E2E",
        "",
        f"- Measurement: `{abnormal['measurement_id']}`",
        f"- ML status: `{abnormal['analysis_result']['status']}`",
        f"- Queries: {len(abnormal['retrieval_queries'])}",
        f"- Evidence: {len(abnormal['rag_evidence'])}",
        f"- Candidates: {len(abnormal['diagnosis_candidates'])}",
        f"- Evidence status: `{abnormal['evidence_status']}`",
        f"- Result: `{abnormal['workflow_status']}/{abnormal['next_action']}`",
        f"- Events: {len(abnormal['events'])}",
        "",
        "## Safety boundaries",
        "",
        "- No raw signal arrays are stored in AgentState.",
        "- Diagnostic queries exclude bearing-specific ground-truth documents.",
        "- The local reasoner does not assert a specific physical root cause.",
        "- No inspection plan, maintenance approval, equipment control, HITL, or SSE is implemented.",
        "- Artifacts omit retrieved source content, prompts, secrets, and private reasoning.",
        "",
    ]
    (artifact_root / "LANGGRAPH_CORE_REPORT.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "normal": {
                    "run_id": normal["run_id"],
                    "status": normal["workflow_status"],
                    "rag_called": bool(normal["retrieval_records"]),
                    "events": len(normal["events"]),
                },
                "abnormal": {
                    "run_id": abnormal["run_id"],
                    "status": abnormal["workflow_status"],
                    "evidence_status": abnormal["evidence_status"],
                    "evidence": len(abnormal["rag_evidence"]),
                    "events": len(abnormal["events"]),
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
