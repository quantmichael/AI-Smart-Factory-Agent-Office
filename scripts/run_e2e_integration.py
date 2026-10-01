"""Generate the STEP 14 MVP-RC1 integration evidence with real ML/RAG inputs."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from time import perf_counter
import sys
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.agent.factory import build_agent_service  # noqa: E402
from app.agent.reasoning import DeterministicEvidenceVerifier  # noqa: E402
from app.agent.run_manager import AgentRunManager  # noqa: E402
from app.agent.schemas import (  # noqa: E402
    AgentRunCreate,
    EvidenceStatus,
    HumanInputSubmission,
    VerificationResult,
)
from app.core.config import Settings, resolve_runtime_path  # noqa: E402
from app.core.readiness import evaluate_readiness  # noqa: E402


class PartialOnceVerifier:
    def __init__(self) -> None:
        self.calls = 0
        self.delegate = DeterministicEvidenceVerifier()

    def verify(self, candidates, evidence):
        self.calls += 1
        if self.calls == 1:
            return VerificationResult(
                status=EvidenceStatus.PARTIAL,
                supported_candidate_ids=[item.candidate_id for item in candidates],
                missing_information=["controlled retry coverage"],
                summary="Controlled STEP 14 PARTIAL result; real retrieval remains in use.",
            )
        return self.delegate.verify(candidates, evidence)


class InsufficientOnceVerifier:
    def __init__(self) -> None:
        self.calls = 0
        self.delegate = DeterministicEvidenceVerifier()

    def verify(self, candidates, evidence):
        self.calls += 1
        if self.calls == 1:
            return VerificationResult(
                status=EvidenceStatus.INSUFFICIENT,
                supported_candidate_ids=[item.candidate_id for item in candidates],
                missing_information=["operator inspection observation"],
                summary="Controlled STEP 14 HITL checkpoint; real ML/RAG remain in use.",
            )
        return self.delegate.verify(candidates, evidence)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n")


def build(settings: Settings, root: Path, *, verifier=None):
    readiness = evaluate_readiness(settings)
    return build_agent_service(
        dataset_root=resolve_runtime_path(settings.paderborn_data_root),
        ml_artifact_root=resolve_runtime_path(settings.ml_artifact_root),
        active_model_id=settings.active_ml_model_id,
        vector_db_path=resolve_runtime_path(settings.vector_db_path),
        checkpoint_path=root / "checkpoints.sqlite3",
        memory_db_path=ARTIFACT_ROOT / "runtime" / "equipment_memory.sqlite3",
        vision_db_path=ARTIFACT_ROOT / "runtime" / "inspection_images.sqlite3",
        vision_upload_root=ARTIFACT_ROOT / "runtime" / "uploads",
        application_version=settings.app_version,
        knowledge_pack_id=settings.knowledge_pack_id,
        knowledge_manifest_version=readiness["versions"]["knowledge_manifest_version"],
        workflow_version=settings.workflow_version,
        evidence_verifier=verifier,
    )


def event_contract(events: list[dict], run_id: str) -> dict:
    sequences = [item["sequence"] for item in events]
    return {
        "unique_sequence": len(sequences) == len(set(sequences)),
        "ordered_sequence": sequences == sorted(sequences),
        "run_id_consistent": all(item["run_id"] == run_id for item in events),
        "roles_present": all(item.get("agent_role") for item in events),
        "completed_event": any(item["event_type"] == "workflow_completed" for item in events),
    }


def completed_nodes(events: list[dict]) -> list[str]:
    return [item["node"] for item in events if item["event_type"] == "node_completed"]


def save_scenario(name: str, state: dict, elapsed_ms: float) -> dict:
    root = ARTIFACT_ROOT / f"{name}_run"
    events = state.get("events", [])
    write_json(root / "run.json", {
        "run_id": state["run_id"], "measurement_id": state["measurement_id"],
        "workflow_status": state["workflow_status"], "version_trace": state["version_trace"],
        "evidence_status": state.get("evidence_status"), "memory_used_ids": state.get("memory_used_ids", []),
        "visual_observations": state.get("visual_observations", []), "elapsed_ms": elapsed_ms,
    })
    write_json(root / "events.json", events)
    write_json(root / "report.json", state.get("final_report"))
    write_json(root / "trace.json", {
        "nodes": completed_nodes(events),
        "queries": state.get("retrieval_queries", []),
        "evidence_ids": [item["evidence_id"] for item in state.get("rag_evidence", [])],
        "diagnosis": state.get("diagnosis_candidates", []),
        "verification": state.get("verification_result"),
        "inspection": state.get("inspection_plan", []),
        "actions": state.get("recommended_actions", []),
        "human_interactions": state.get("human_interactions", []),
        "node_timings": state.get("node_timings", []),
        "event_contract": event_contract(events, state["run_id"]),
    })
    return {"run_id": state["run_id"], "status": state["workflow_status"], "elapsed_ms": elapsed_ms, "nodes": completed_nodes(events)}


def run_direct(workflow, measurement_id: str, run_id: str, **kwargs):
    started = perf_counter()
    state = workflow.start_run(measurement_id, run_id=run_id, **kwargs)
    return state, (perf_counter() - started) * 1000


ARTIFACT_ROOT = PROJECT_ROOT / "artifacts" / "e2e"


def main() -> None:
    settings = Settings()
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    registry = json.loads((PROJECT_ROOT / "config" / "demo_scenarios.json").read_text())
    scenarios = {item["scenario_id"]: item for item in registry["scenarios"]}
    readiness = evaluate_readiness(settings)
    if readiness["status"] != "ready":
        raise RuntimeError(f"readiness failed: {readiness}")
    write_json(ARTIFACT_ROOT / "readiness.json", readiness)

    default_root = ARTIFACT_ROOT / "runtime" / "default"
    workflow = build(settings, default_root)
    manager = AgentRunManager(workflow, ARTIFACT_ROOT / "runtime" / "agent_runs.sqlite3", max_workers=1)
    scenario_results: dict[str, dict] = {}

    start = perf_counter()
    normal_created = manager.create_run(AgentRunCreate(
        equipment_id="paderborn-bearing-test-rig",
        measurement_id=scenarios["normal"]["measurement_id"],
    ))
    manager.wait_for_status(normal_created.run_id, {"COMPLETED"}, timeout_seconds=30)
    normal_state = workflow.get_run(normal_created.run_id)
    scenario_results["normal"] = save_scenario("normal", normal_state, (perf_counter() - start) * 1000)

    image_content = (PROJECT_ROOT / scenarios["abnormal_multimodal"]["optional_image"]).read_bytes()
    image = workflow.dependencies.vision_service.store(
        equipment_id="paderborn-bearing-test-rig", content=image_content,
        mime_type="image/png", filename="simulated_inspection_input.png",
        description="Simulated demo input; not synchronized Paderborn ground truth.",
    )
    start = perf_counter()
    abnormal_created = manager.create_run(AgentRunCreate(
        equipment_id="paderborn-bearing-test-rig",
        measurement_id=scenarios["abnormal_multimodal"]["measurement_id"],
        inspection_image_ids=[image.image_id],
    ))
    manager.wait_for_status(abnormal_created.run_id, {"COMPLETED"}, timeout_seconds=30)
    abnormal_state = workflow.get_run(abnormal_created.run_id)
    scenario_results["abnormal"] = save_scenario("abnormal", abnormal_state, (perf_counter() - start) * 1000)

    all_events = manager.get_events(abnormal_created.run_id)
    midpoint = all_events[len(all_events) // 2].sequence
    reconnect_events = manager.get_events(abnormal_created.run_id, after_sequence=midpoint)
    refresh_reconnect = {
        "full_reload_event_count": len(all_events),
        "resume_after_sequence": midpoint,
        "reconnected_event_count": len(reconnect_events),
        "reconnect_suffix_valid": all(item.sequence > midpoint for item in reconnect_events),
        "run_state_reload": manager.get_run(abnormal_created.run_id).workflow_status.value == "COMPLETED",
    }
    manager.close()

    restarted_workflow = build(settings, default_root)
    restarted_manager = AgentRunManager(restarted_workflow, ARTIFACT_ROOT / "runtime" / "agent_runs.sqlite3", max_workers=1)
    refresh_reconnect["restart_run_readable"] = restarted_manager.get_run(abnormal_created.run_id).workflow_status.value == "COMPLETED"
    refresh_reconnect["restart_events_readable"] = bool(restarted_manager.get_events(abnormal_created.run_id))
    refresh_reconnect["restart_report_readable"] = restarted_manager.get_report(abnormal_created.run_id).run_id == abnormal_created.run_id
    restarted_manager.close()
    write_json(ARTIFACT_ROOT / "refresh_reconnect.json", refresh_reconnect)

    retry_workflow = build(settings, ARTIFACT_ROOT / "runtime" / "retry", verifier=PartialOnceVerifier())
    retry_state, retry_ms = run_direct(retry_workflow, scenarios["rag_retry_controlled"]["measurement_id"], f"run_retry_{uuid4().hex[:16]}")
    retry_workflow.dependencies.memory_service.record_run_memory(retry_state)
    scenario_results["retry"] = save_scenario("retry", retry_state, retry_ms)
    retry_workflow.close()

    hitl_workflow = build(settings, ARTIFACT_ROOT / "runtime" / "hitl", verifier=InsufficientOnceVerifier())
    hitl_started = perf_counter()
    waiting = hitl_workflow.start_run(scenarios["hitl_controlled"]["measurement_id"], run_id=f"run_hitl_{uuid4().hex[:16]}")
    if waiting["workflow_status"] != "WAITING":
        raise AssertionError("controlled HITL scenario did not wait")
    request = waiting["pending_human_request"]
    response = {field: ("외관상 즉시 확인 가능한 이상 없음" if field == "inspection_observation" else "N09_M07_F10 확인") for field in request["requested_fields"]}
    hitl_state = hitl_workflow.submit_human_input(
        waiting["run_id"],
        HumanInputSubmission(request_id=request["request_id"], response=response, actor="step14-validation"),
    )
    hitl_ms = (perf_counter() - hitl_started) * 1000
    hitl_workflow.dependencies.memory_service.record_run_memory(hitl_state)
    scenario_results["hitl"] = save_scenario("hitl", hitl_state, hitl_ms)
    hitl_workflow.close()

    manifest = json.loads((resolve_runtime_path(settings.knowledge_base_root) / settings.knowledge_pack_id / "manifests" / "source_manifest.json").read_text())
    manifest_sources = {item["source_id"] for item in manifest["sources"]}
    evidence_ids = {item["evidence_id"] for item in abnormal_state["rag_evidence"]}
    citation_audit = all(
        citation["evidence_id"] in evidence_ids
        and next(item for item in abnormal_state["rag_evidence"] if item["evidence_id"] == citation["evidence_id"])["source_id"] in manifest_sources
        for citation in abnormal_state["final_report"]["citations"]
    )
    serialized_context = json.dumps({
        "measurement_ref": abnormal_state.get("measurement_ref"),
        "analysis": abnormal_state.get("analysis_result"),
        "queries": abnormal_state.get("retrieval_queries"),
        "diagnosis": abnormal_state.get("diagnosis_candidates"),
    }).lower()
    audits = {
        "ground_truth_leakage": not any(term in serialized_context for term in ["ground_truth", "damage_location", "fact_sheet_answer"]),
        "citation_trace_to_manifest": citation_audit,
        "unsupported_evidence_references": all(set(item["supporting_evidence_ids"]).issubset(evidence_ids) for item in abnormal_state["diagnosis_candidates"]),
        "automatic_control_absent": all(item["action_type"] != "AUTOMATIC_CONTROL" for item in abnormal_state["recommended_actions"]),
        "memory_used_on_second_run": bool(abnormal_state.get("memory_used_ids")),
        "fake_maintenance_absent": not workflow.dependencies.memory_service.repository.list_maintenance("paderborn-bearing-test-rig"),
        "multimodal_relationship_disclosed": "not synchronized Paderborn ground truth" in image.description,
        "visual_not_fault_diagnosis": all(item["category"] == "image_quality" for result in abnormal_state["visual_observations"] for item in result["observations"]),
    }
    write_json(ARTIFACT_ROOT / "audit_results.json", audits)

    expected = {item["scenario_id"]: item["expected_route"] for item in registry["scenarios"]}
    actual = {
        "normal": scenario_results["normal"]["nodes"],
        "abnormal_multimodal": scenario_results["abnormal"]["nodes"],
        "rag_retry_controlled": scenario_results["retry"]["nodes"],
        "hitl_controlled": scenario_results["hitl"]["nodes"],
    }
    route_validation = {
        key: {
            "expected_subsequence": value,
            "actual": actual[key],
            "pass": all(node in actual[key] for node in value),
        }
        for key, value in expected.items()
    }
    write_json(ARTIFACT_ROOT / "route_validation.json", route_validation)

    scenario_states = {
        "normal": normal_state,
        "abnormal": abnormal_state,
        "retry": retry_state,
        "hitl": hitl_state,
    }
    metric_nodes = {
        "ml_ms": {"run_detection"},
        "rag_ms": {"retrieve_knowledge", "build_rag_query", "refine_query"},
        "reasoning_ms": {"diagnose", "verify_evidence"},
        "vision_ms": {"analyze_inspection_image", "merge_visual_context"},
        "memory_ms": {"load_equipment_memory"},
    }
    metrics = {}
    for key, value in scenario_results.items():
        timings = scenario_states[key].get("node_timings", [])
        metrics[key] = {"total_ms": round(value["elapsed_ms"], 3)}
        metrics[key].update({
            label: round(sum(float(item["duration_ms"]) for item in timings if item["node"] in nodes), 3)
            for label, nodes in metric_nodes.items()
        })
    metrics["note"] = "Reasoning is the deterministic local provider in MVP-RC1; no external LLM token cost was incurred."
    write_json(ARTIFACT_ROOT / "e2e_metrics.json", metrics)
    p0 = []
    if not all(audits.values()): p0.append("audit failure")
    if not all(item["pass"] for item in route_validation.values()): p0.append("route mismatch")
    if not all(value["status"] == "COMPLETED" for value in scenario_results.values()): p0.append("incomplete scenario")
    report = f"""# STEP 14 E2E Integration Report — MVP-RC1

- Generated: {datetime.now(UTC).isoformat()}
- Readiness: `{readiness['status']}`
- Normal: `{scenario_results['normal']['run_id']}` / `{scenario_results['normal']['status']}`
- Abnormal + Multimodal: `{scenario_results['abnormal']['run_id']}` / `{scenario_results['abnormal']['status']}`
- Controlled RAG Retry: `{scenario_results['retry']['run_id']}` / `{scenario_results['retry']['status']}`
- Controlled HITL: `{scenario_results['hitl']['run_id']}` / `{scenario_results['hitl']['status']}`
- Memory on second run: `{audits['memory_used_on_second_run']}`
- Refresh/reconnect/restart: `{all(refresh_reconnect.values())}`
- Citation trace: `{audits['citation_trace_to_manifest']}`
- Ground-truth leakage audit: `{audits['ground_truth_leakage']}`
- P0 bugs: `{len(p0)}`

Retry and HITL routing decisions are explicitly controlled test conditions. They
still use the actual Paderborn measurement, active ML artifact, and bearing_v1
vector database. The inspection image is simulated and is not synchronized with
the Paderborn vibration measurement.
"""
    (ARTIFACT_ROOT / "E2E_INTEGRATION_REPORT.md").write_text(report)
    print(json.dumps({"release": "MVP-RC1", "scenarios": scenario_results, "p0": p0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
