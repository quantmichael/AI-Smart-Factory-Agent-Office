"""Single-responsibility nodes for the STEP 08 diagnosis graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import hashlib
from time import perf_counter
from typing import Any

from app.agent.events import make_error_event, make_events
from app.agent.actions import ActionPlanner
from app.agent.policies import ActionPolicy
from app.agent.reasoning import DiagnosisReasoner, EvidenceVerifier
from app.agent.schemas import (
    ActionPriority,
    ActionType,
    ApprovalDecision,
    DiagnosisCandidate,
    FinalReport,
    HumanInputSubmission,
    HumanInteraction,
    HumanRequest,
    HumanRequestType,
    InspectionStep,
    RecommendedAction,
    ReportCitation,
    validate_plan_references,
)
from app.agent.state import AgentState
from app.domain.schemas import AnalysisResult, EvidenceObject, WorkflowStatus
from app.rag.retrieval import (
    QueryBuilder,
    RetrievalContext,
    RetrievalMode,
    RetrievalPurpose,
    RetrievalQuery,
    RetrieverService,
)
from app.services.analysis import AnalysisApplicationService


@dataclass(slots=True)
class AgentDependencies:
    analysis_service: AnalysisApplicationService
    retriever: RetrieverService
    diagnosis_reasoner: DiagnosisReasoner
    evidence_verifier: EvidenceVerifier
    action_planner: ActionPlanner
    action_policy: ActionPolicy
    max_retrieval_retries: int = 2
    max_human_information_rounds: int = 2
    max_action_revision_rounds: int = 1
    memory_service: Any | None = None
    vision_service: Any | None = None
    version_trace: dict[str, str] = field(default_factory=lambda: {
        "application_version": "test",
        "model_id": "unknown",
        "model_version": "unknown",
        "knowledge_pack_id": "bearing_v1",
        "knowledge_manifest_version": "unknown",
        "workflow_version": "diagnosis_core_v1",
    })


class AgentNodes:
    def __init__(self, dependencies: AgentDependencies) -> None:
        self.dependencies = dependencies
        self.query_builder = QueryBuilder()

    @staticmethod
    def _timing(node: str, started: float) -> list[dict[str, Any]]:
        return [{"node": node, "duration_ms": (perf_counter() - started) * 1000.0}]

    def _failure(
        self,
        state: AgentState,
        node: str,
        error_type: str,
        exc: Exception,
        started: float,
    ) -> dict[str, Any]:
        return {
            "current_node": node,
            "workflow_status": WorkflowStatus.FAILED.value,
            "errors": [
                *state.get("errors", []),
                {
                    "error_type": error_type,
                    "node": node,
                    "exception_type": type(exc).__name__,
                },
            ],
            "events": [make_error_event(state, node, error_type)],
            "node_timings": self._timing(node, started),
        }

    def initialize_run(self, state: AgentState) -> dict[str, Any]:
        started = perf_counter()
        update = {
            "retrieval_retry_count": state.get("retrieval_retry_count", 0),
            "max_retrieval_retries": state.get(
                "max_retrieval_retries", self.dependencies.max_retrieval_retries
            ),
            "workflow_status": WorkflowStatus.RUNNING.value,
            "current_node": "initialize_run",
            "errors": state.get("errors", []),
            "reasoning_provider": self.dependencies.diagnosis_reasoner.provider_id,
            "human_information_round_count": state.get("human_information_round_count", 0),
            "max_human_information_rounds": state.get(
                "max_human_information_rounds",
                self.dependencies.max_human_information_rounds,
            ),
            "action_revision_count": state.get("action_revision_count", 0),
            "max_action_revision_rounds": state.get(
                "max_action_revision_rounds",
                self.dependencies.max_action_revision_rounds,
            ),
        }
        event_state = {**state, **update}
        update["events"] = make_events(
            event_state,
            "initialize_run",
            "Workflow initialized.",
            payload={"max_retrieval_retries": update["max_retrieval_retries"]},
            workflow_started=True,
        )
        update["node_timings"] = self._timing("initialize_run", started)
        return update

    def load_sensor_data(self, state: AgentState) -> dict[str, Any]:
        node, started = "load_sensor_data", perf_counter()
        try:
            summary = self.dependencies.analysis_service.adapter.get_metadata(
                state["measurement_id"]
            )
            update = {
                "equipment_id": summary.equipment_id,
                "measurement_ref": {
                    "measurement_id": summary.measurement_id,
                    "equipment_id": summary.equipment_id,
                    "source": summary.source,
                    "metadata": {"bearing_id": summary.bearing_id},
                },
                "operating_condition": summary.operating_condition.model_dump(mode="json"),
                "current_node": node,
            }
            update["events"] = make_events(
                state,
                node,
                "Measurement metadata loaded.",
                payload={"measurement_id": summary.measurement_id},
            )
            update["node_timings"] = self._timing(node, started)
            return update
        except Exception as exc:
            return self._failure(state, node, "DATA_ERROR", exc, started)

    def run_detection(self, state: AgentState) -> dict[str, Any]:
        node, started = "run_detection", perf_counter()
        try:
            result = self.dependencies.analysis_service.analyze(state["measurement_id"])
            update = {
                "analysis_result": result.model_dump(mode="json"),
                "current_node": node,
                "events": make_events(
                    state,
                    node,
                    "ML detection completed.",
                    payload={
                        "status": result.status.value,
                        "predicted_class": result.predicted_class,
                        "confidence": result.confidence,
                        "model_id": result.model_id,
                    },
                    extra_events=[
                        (
                            f"detection_{result.status.value}",
                            f"Detection result is {result.status.value}.",
                        )
                    ],
                ),
                "node_timings": self._timing(node, started),
            }
            return update
        except Exception as exc:
            return self._failure(state, node, "ML_ERROR", exc, started)

    def load_equipment_memory(self, state: AgentState) -> dict[str, Any]:
        node, started = "load_equipment_memory", perf_counter()
        service = self.dependencies.memory_service
        if service is None:
            context = {
                "equipment_id": state["equipment_id"],
                "recent_measurements": [], "recent_analyses": [],
                "previous_diagnoses": [], "human_observations": [],
                "maintenance_history": [], "unresolved_items": [],
                "memory_used_ids": [],
            }
        else:
            context = service.get_relevant_context(
                state["equipment_id"],
                operating_condition=state.get("operating_condition", {}).get("code"),
            ).model_dump(mode="json")
        return {
            "equipment_memory": context,
            "memory_used_ids": context["memory_used_ids"],
            "current_node": node,
            "events": make_events(
                state, node, "Relevant equipment history loaded.",
                payload={"memory_count": len(context["memory_used_ids"])},
                extra_events=[("equipment_memory_loaded", "Equipment memory context loaded.")],
            ),
            "node_timings": self._timing(node, started),
        }

    def check_abnormal(self, state: AgentState) -> dict[str, Any]:
        node, started = "check_abnormal", perf_counter()
        status = state["analysis_result"]["status"]
        return {
            "current_node": node,
            "events": make_events(
                state, node, f"Analysis routed to the {status} path.", payload={"status": status}
            ),
            "node_timings": self._timing(node, started),
        }

    def check_inspection_image(self, state: AgentState) -> dict[str, Any]:
        node, started = "check_inspection_image", perf_counter()
        count = len(state.get("inspection_image_ids", []))
        return {
            "current_node": node,
            "events": make_events(
                state,
                node,
                "Optional inspection image route evaluated.",
                payload={"image_count": count},
                extra_events=(
                    [("inspection_image_uploaded", "Inspection image is available for this run.")]
                    if count else []
                ),
            ),
            "node_timings": self._timing(node, started),
        }

    def analyze_inspection_image(self, state: AgentState) -> dict[str, Any]:
        node, started = "analyze_inspection_image", perf_counter()
        service = self.dependencies.vision_service
        results: list[dict[str, Any]] = []
        if service is not None:
            for image_id in state.get("inspection_image_ids", []):
                results.append(service.analyze(image_id).model_dump(mode="json"))
        failures = sum(bool(item.get("analysis_error")) for item in results)
        observations = sum(len(item.get("observations", [])) for item in results)
        return {
            "visual_observations": results,
            "current_node": node,
            "events": make_events(
                state,
                node,
                "Inspection image observation completed.",
                payload={"image_count": len(results), "observation_count": observations, "failure_count": failures},
                extra_events=[
                    ("vision_analysis_completed", "Visual observation analysis completed.")
                ],
            ),
            "node_timings": self._timing(node, started),
        }

    def merge_visual_context(self, state: AgentState) -> dict[str, Any]:
        node, started = "merge_visual_context", perf_counter()
        count = sum(len(item.get("observations", [])) for item in state.get("visual_observations", []))
        return {
            "current_node": node,
            "events": make_events(
                state, node, "Visual observations added as a separate diagnosis context.",
                payload={"observation_count": count},
                extra_events=[("visual_context_added", "Visual context added separately from technical evidence.")],
            ),
            "node_timings": self._timing(node, started),
        }

    def save_normal_state(self, state: AgentState) -> dict[str, Any]:
        node, started = "save_normal_state", perf_counter()
        return {
            "current_node": node,
            "next_action": "MONITOR",
            "events": make_events(state, node, "Normal analysis state recorded."),
            "node_timings": self._timing(node, started),
        }

    def generate_normal_report(self, state: AgentState) -> dict[str, Any]:
        node, started = "generate_normal_report", perf_counter()
        analysis = state["analysis_result"]
        report = FinalReport(
            run_id=state["run_id"],
            equipment_id=state["equipment_id"],
            measurement_id=state["measurement_id"],
            demo_scenario=state.get("demo_scenario"),
            analysis_summary={
                "analysis_id": analysis["analysis_id"],
                "status": analysis["status"],
                "predicted_class": analysis["predicted_class"],
                "model_id": analysis["model_id"],
                "signal_features": analysis["signal_features"],
            },
            diagnosis_candidates=[],
            inspection_plan=[],
            recommended_actions=[],
            human_interactions=[],
            limitations=[
                "The model classified this measurement as normal; this does not guarantee "
                "the absence of every equipment issue. Continue routine monitoring."
            ],
            citations=[],
            historical_context_used=state.get("memory_used_ids", []),
            version_trace=state["version_trace"],
            created_at=datetime.now(UTC),
        ).model_dump(mode="json")
        return {
            "current_node": node,
            "workflow_status": WorkflowStatus.COMPLETED.value,
            "final_report": report,
            "events": make_events(
                state,
                node,
                "Normal analysis report generated.",
                extra_events=[
                    ("report_generated", "Final report generated."),
                    ("workflow_completed", "Workflow completed."),
                ],
            ),
            "node_timings": self._timing(node, started),
        }

    def _retrieval_context(self, state: AgentState) -> RetrievalContext:
        analysis = AnalysisResult.model_validate(state["analysis_result"])
        return RetrievalContext(
            analysis_id=analysis.analysis_id,
            measurement_id=analysis.measurement_id,
            status=analysis.status.value,
            predicted_class=analysis.predicted_class,
            confidence=analysis.confidence,
            signal_features=analysis.signal_features,
            bearing_id=state["measurement_ref"]["metadata"].get("bearing_id"),
            operating_condition=state["operating_condition"].get("code"),
            mode=RetrievalMode.DIAGNOSTIC,
        )

    def build_rag_query(self, state: AgentState) -> dict[str, Any]:
        node, started = "build_rag_query", perf_counter()
        context = self._retrieval_context(state)
        queries = [
            self.query_builder.build(context, purpose, top_k=5)
            for purpose in (
                RetrievalPurpose.DIAGNOSTIC_EVIDENCE,
                RetrievalPurpose.INSPECTION_ACTION,
            )
        ]
        observations = state.get("human_observations", [])
        if observations:
            observation_text = " ".join(
                f"human observation {item['type']} {item['value']}"
                for item in observations[-8:]
            )
            queries.append(
                self.query_builder.build_text_query(
                    observation_text,
                    RetrievalPurpose.DIAGNOSTIC_EVIDENCE,
                    top_k=5,
                )
            )
        visible_terms = [
            item["description"]
            for result in state.get("visual_observations", [])
            if result.get("quality") == "USABLE"
            for item in result.get("observations", [])
            if item.get("category") != "image_quality"
        ]
        if visible_terms:
            queries.append(
                self.query_builder.build_text_query(
                    "visible exterior observation " + " ".join(visible_terms[:4]),
                    RetrievalPurpose.INSPECTION_ACTION,
                    top_k=5,
                )
            )
        serialized = [item.model_dump(mode="json") for item in queries]
        return {
            "pending_queries": serialized,
            "retrieval_queries": serialized,
            "current_node": node,
            "events": make_events(
                state,
                node,
                "Purpose-specific RAG queries built.",
                payload={"query_count": len(queries)},
            ),
            "node_timings": self._timing(node, started),
        }

    def retrieve_knowledge(self, state: AgentState) -> dict[str, Any]:
        node, started = "retrieve_knowledge", perf_counter()
        try:
            existing = {
                item["chunk_id"]: item for item in state.get("rag_evidence", [])
            }
            records = list(state.get("retrieval_records", []))
            pending_queries = state.get("pending_queries", [])
            for raw_query in pending_queries:
                result = self.dependencies.retriever.retrieve(
                    RetrievalQuery.model_validate(raw_query)
                )
                for evidence in result.evidence:
                    existing.setdefault(
                        evidence.chunk_id, evidence.model_dump(mode="json")
                    )
                records.append(
                    {
                        "query": result.query.model_dump(mode="json"),
                        "stats": result.stats.model_dump(mode="json"),
                        "evidence_ids": [item.evidence_id for item in result.evidence],
                    }
                )
            evidence = list(existing.values())
            return {
                "rag_evidence": evidence,
                "retrieval_records": records,
                "pending_queries": [],
                "current_node": node,
                "events": make_events(
                    state,
                    node,
                    "Technical evidence retrieved.",
                    payload={
                        "evidence_count": len(evidence),
                        "retry_count": state.get("retrieval_retry_count", 0),
                        "queries": [
                            {"query_id": item["query_id"], "purpose": item["purpose"]}
                            for item in pending_queries
                        ],
                    },
                    extra_events=[("retrieval_completed", "Evidence retrieval completed.")],
                ),
                "node_timings": self._timing(node, started),
            }
        except Exception as exc:
            return self._failure(state, node, "RAG_ERROR", exc, started)

    def diagnose(self, state: AgentState) -> dict[str, Any]:
        node, started = "diagnose", perf_counter()
        try:
            analysis = AnalysisResult.model_validate(state["analysis_result"])
            evidence = [EvidenceObject.model_validate(item) for item in state.get("rag_evidence", [])]
            candidates = self.dependencies.diagnosis_reasoner.diagnose(
                analysis,
                evidence,
                equipment_memory=state.get("equipment_memory", {}),
                visual_observations=state.get("visual_observations", []),
            )
            serialized = [item.model_dump(mode="json") for item in candidates]
            return {
                "diagnosis_candidates": serialized,
                "current_node": node,
                "events": make_events(
                    state,
                    node,
                    "Evidence-grounded diagnosis candidates created.",
                    payload={
                        "candidate_count": len(candidates),
                        "memory_used_ids": state.get("memory_used_ids", []),
                        "visual_observation_ids": [
                            observation["observation_id"]
                            for result in state.get("visual_observations", [])
                            for observation in result.get("observations", [])
                        ],
                        "context_sections": [
                            "CURRENT_SENSOR_ANALYSIS", "VISUAL_OBSERVATIONS",
                            "TECHNICAL_EVIDENCE", "EQUIPMENT_MEMORY", "HUMAN_OBSERVATIONS"
                        ],
                    },
                ),
                "node_timings": self._timing(node, started),
            }
        except Exception as exc:
            return self._failure(state, node, "LLM_ERROR", exc, started)

    def verify_evidence(self, state: AgentState) -> dict[str, Any]:
        node, started = "verify_evidence", perf_counter()
        try:
            candidates = [
                DiagnosisCandidate.model_validate(item)
                for item in state.get("diagnosis_candidates", [])
            ]
            evidence = [EvidenceObject.model_validate(item) for item in state.get("rag_evidence", [])]
            result = self.dependencies.evidence_verifier.verify(candidates, evidence)
            return {
                "verification_result": result.model_dump(mode="json"),
                "evidence_status": result.status.value,
                "current_node": node,
                "events": make_events(
                    state,
                    node,
                    "Evidence coverage verified.",
                    payload={
                        "evidence_status": result.status.value,
                        "retry_count": state.get("retrieval_retry_count", 0),
                    },
                    extra_events=[
                        ("evidence_status_changed", "Evidence status evaluated.")
                    ],
                ),
                "node_timings": self._timing(node, started),
            }
        except Exception as exc:
            return self._failure(state, node, "LLM_ERROR", exc, started)

    def refine_query(self, state: AgentState) -> dict[str, Any]:
        node, started = "refine_query", perf_counter()
        retry = state.get("retrieval_retry_count", 0) + 1
        missing = state.get("verification_result", {}).get("missing_information", [])
        purpose = (
            RetrievalPurpose.INSPECTION_ACTION
            if any("inspection" in item for item in missing)
            else RetrievalPurpose.DIAGNOSTIC_EVIDENCE
        )
        text = (
            "bearing technical evidence needed to address "
            + ", ".join(missing or ["missing diagnostic context"])
            + f" workflow refinement {retry}"
        )
        query = self.query_builder.build_text_query(text, purpose, top_k=5)
        serialized = query.model_dump(mode="json")
        return {
            "retrieval_retry_count": retry,
            "pending_queries": [serialized],
            "retrieval_queries": [*state.get("retrieval_queries", []), serialized],
            "current_node": node,
            "events": make_events(
                state, node, "Retrieval query refined.", payload={"retry_count": retry}
            ),
            "node_timings": self._timing(node, started),
        }

    def retrieve_counter_evidence(self, state: AgentState) -> dict[str, Any]:
        node, started = "retrieve_counter_evidence", perf_counter()
        retry = state.get("retrieval_retry_count", 0) + 1
        query = self.query_builder.build_text_query(
            "bearing alternative explanation contradictory conditions counter evidence inspection",
            RetrievalPurpose.DIAGNOSTIC_EVIDENCE,
            top_k=5,
        )
        serialized = query.model_dump(mode="json")
        return {
            "retrieval_retry_count": retry,
            "pending_queries": [serialized],
            "retrieval_queries": [*state.get("retrieval_queries", []), serialized],
            "current_node": node,
            "events": make_events(
                state,
                node,
                "Counter-evidence query built.",
                payload={"retry_count": retry},
            ),
            "node_timings": self._timing(node, started),
        }

    def ready_for_inspection(self, state: AgentState) -> dict[str, Any]:
        node, started = "ready_for_inspection", perf_counter()
        report = {
            "report_type": "core_diagnostic_summary",
            "measurement_id": state["measurement_id"],
            "analysis_id": state["analysis_result"]["analysis_id"],
            "analysis_status": state["analysis_result"]["status"],
            "diagnosis_candidates": state.get("diagnosis_candidates", []),
            "evidence_status": state["evidence_status"],
            "summary": (
                "The core workflow has enough evidence to proceed to inspection planning. "
                "No physical fault or maintenance action has been approved."
            ),
        }
        return {
            "workflow_status": WorkflowStatus.COMPLETED.value,
            "next_action": "READY_FOR_INSPECTION",
            "final_report": report,
            "current_node": node,
            "events": make_events(
                state,
                node,
                "Core diagnosis is ready for inspection planning.",
                payload={"evidence_status": state["evidence_status"]},
            ),
            "node_timings": self._timing(node, started),
        }

    def needs_additional_information(self, state: AgentState) -> dict[str, Any]:
        node, started = "needs_additional_information", perf_counter()
        verification = state.get("verification_result") or {}
        request = {
            "reason": state.get("evidence_status", "INSUFFICIENT"),
            "missing_information": verification.get("missing_information", []),
            "conflicts": verification.get("conflicts", []),
            "retry_count": state.get("retrieval_retry_count", 0),
        }
        return {
            "workflow_status": WorkflowStatus.WAITING.value,
            "next_action": "ADDITIONAL_INFORMATION_REQUIRED",
            "additional_information_request": request,
            "current_node": node,
            "events": make_events(
                state,
                node,
                "Additional information is required.",
                payload={
                    "evidence_status": state.get("evidence_status"),
                    "retry_count": state.get("retrieval_retry_count", 0),
                },
            ),
            "node_timings": self._timing(node, started),
        }

    def build_inspection_plan(self, state: AgentState) -> dict[str, Any]:
        node, started = "build_inspection_plan", perf_counter()
        try:
            candidates = [
                DiagnosisCandidate.model_validate(item)
                for item in state.get("diagnosis_candidates", [])
            ]
            evidence = [EvidenceObject.model_validate(item) for item in state.get("rag_evidence", [])]
            steps = self.dependencies.action_planner.build_inspection_plan(candidates, evidence)
            validate_plan_references(
                steps,
                {item.candidate_id for item in candidates},
                {item.evidence_id for item in evidence},
            )
            return {
                "inspection_plan": [item.model_dump(mode="json") for item in steps],
                "current_node": node,
                "events": make_events(
                    state,
                    node,
                    "Evidence-linked inspection plan created.",
                    payload={"inspection_step_count": len(steps)},
                    extra_events=[
                        ("inspection_plan_created", "Inspection plan created.")
                    ],
                ),
                "node_timings": self._timing(node, started),
            }
        except Exception as exc:
            return self._failure(state, node, "LLM_ERROR", exc, started)

    def recommend_action(self, state: AgentState) -> dict[str, Any]:
        node, started = "recommend_action", perf_counter()
        try:
            candidates = [DiagnosisCandidate.model_validate(item) for item in state["diagnosis_candidates"]]
            evidence = [EvidenceObject.model_validate(item) for item in state["rag_evidence"]]
            plan = [InspectionStep.model_validate(item) for item in state["inspection_plan"]]
            drafted = self.dependencies.action_planner.recommend_action(
                candidates, evidence, plan
            )
            draft_models = [RecommendedAction.model_validate(item) for item in drafted]
            controlled_hitl = state.get("demo_scenario") == "HITL_CONTROLLED"
            if controlled_hitl:
                draft_models = [
                    item.model_copy(
                        update={
                            "action_type": ActionType.SHUTDOWN_CHECK,
                            "priority": ActionPriority.HIGH,
                            "summary": (
                                "Controlled HITL demo: ask the operator to review whether "
                                "a controlled stop check is needed."
                            ),
                            "reason": (
                                "This disclosed demo condition validates the human approval "
                                "and checkpoint-resume path; it does not issue an equipment command. "
                                + item.reason
                            ),
                            "limitations": list(
                                dict.fromkeys(
                                    [
                                        *item.limitations,
                                        "Controlled HITL demonstration only; not an automatic shutdown command.",
                                    ]
                                )
                            ),
                        }
                    )
                    for item in draft_models
                ]
            valid_ids = {item.evidence_id for item in evidence}
            actions = [
                self.dependencies.action_policy.apply(
                    item,
                    valid_evidence_ids=valid_ids,
                )
                for item in draft_models
            ]
            return {
                "recommended_actions": [item.model_dump(mode="json") for item in actions],
                "current_node": node,
                "events": make_events(
                    state,
                    node,
                    "Evidence-linked actions recommended.",
                    payload={
                        "action_count": len(actions),
                        "approval_required": any(
                            item.requires_human_approval for item in actions
                        ),
                        "demo_scenario": state.get("demo_scenario"),
                    },
                    extra_events=[("action_recommended", "Action recommendation created.")],
                ),
                "node_timings": self._timing(node, started),
            }
        except Exception as exc:
            return self._failure(state, node, "LLM_ERROR", exc, started)

    def check_human_approval(self, state: AgentState) -> dict[str, Any]:
        node, started = "check_human_approval", perf_counter()
        required = any(
            item.get("requires_human_approval")
            for item in state.get("recommended_actions", [])
        )
        return {
            "current_node": node,
            "events": make_events(
                state,
                node,
                "Human approval policy evaluated.",
                payload={"approval_required": required},
            ),
            "node_timings": self._timing(node, started),
        }

    @staticmethod
    def _request_id(state: AgentState, request_type: str, suffix: str) -> str:
        identity = f"{state['run_id']}:{request_type}:{suffix}"
        return "request_" + hashlib.sha256(identity.encode()).hexdigest()[:20]

    def request_human_approval(self, state: AgentState) -> dict[str, Any]:
        node, started = "request_human_approval", perf_counter()
        action = next(
            item
            for item in state.get("recommended_actions", [])
            if item["requires_human_approval"]
        )
        request = HumanRequest(
            request_id=self._request_id(
                state,
                HumanRequestType.APPROVAL.value,
                f"{action['action_id']}:{state.get('action_revision_count', 0)}",
            ),
            run_id=state["run_id"],
            request_type=HumanRequestType.APPROVAL,
            question="Review the recommended action and record a workflow decision.",
            reason=action["reason"],
            related_candidate_ids=[
                item["candidate_id"] for item in state.get("diagnosis_candidates", [])
            ],
            action_id=action["action_id"],
            created_at=datetime.now(UTC),
        )
        return {
            "pending_human_request": request.model_dump(mode="json"),
            "workflow_status": WorkflowStatus.WAITING.value,
            "next_action": "HUMAN_APPROVAL_REQUIRED",
            "current_node": node,
            "events": make_events(
                state,
                node,
                "Human approval requested.",
                payload={"request_id": request.request_id, "action_id": action["action_id"]},
                extra_events=[("human_input_required", "Human approval is required.")],
            ),
            "node_timings": self._timing(node, started),
        }

    def request_additional_information(self, state: AgentState) -> dict[str, Any]:
        node, started = "request_additional_information", perf_counter()
        verification = state.get("verification_result") or {}
        missing = verification.get("missing_information", [])
        requested = ["inspection_observation", "operating_condition_confirmation"]
        if any("image" in item.lower() for item in missing):
            requested = ["inspection_image_id"]
        if any("maintenance" in item.lower() for item in missing):
            requested.append("maintenance_history")
        round_number = state.get("human_information_round_count", 0) + 1
        request = HumanRequest(
            request_id=self._request_id(
                state, HumanRequestType.ADDITIONAL_INFORMATION.value, str(round_number)
            ),
            run_id=state["run_id"],
            request_type=HumanRequestType.ADDITIONAL_INFORMATION,
            question="Provide the requested observations without changing the ML analysis result.",
            requested_fields=requested,
            reason="; ".join(missing) or "Additional evidence context is required.",
            related_candidate_ids=[
                item["candidate_id"] for item in state.get("diagnosis_candidates", [])
            ],
            created_at=datetime.now(UTC),
        )
        return {
            "pending_human_request": request.model_dump(mode="json"),
            "workflow_status": WorkflowStatus.WAITING.value,
            "next_action": "ADDITIONAL_INFORMATION_REQUIRED",
            "current_node": node,
            "events": make_events(
                state,
                node,
                "Additional information requested.",
                payload={"request_id": request.request_id, "requested_fields": requested},
                extra_events=[("human_input_required", "Additional information is required.")],
            ),
            "node_timings": self._timing(node, started),
        }

    def await_human_input(self, state: AgentState) -> dict[str, Any]:
        from langgraph.types import interrupt

        node, started = "await_human_input", perf_counter()
        submission = HumanInputSubmission.model_validate(
            interrupt(state["pending_human_request"])
        )
        return {
            "human_input": submission.model_dump(mode="json"),
            "workflow_status": WorkflowStatus.RUNNING.value,
            "next_action": None,
            "current_node": node,
            "events": make_events(
                state,
                node,
                "Human input received and workflow resumed.",
                payload={"request_id": submission.request_id},
                extra_events=[
                    ("human_input_received", "Human input received."),
                    ("workflow_resumed", "Workflow resumed from checkpoint."),
                ],
            ),
            "node_timings": self._timing(node, started),
        }

    def resume_after_human(self, state: AgentState) -> dict[str, Any]:
        node, started = "resume_after_human", perf_counter()
        request = HumanRequest.model_validate(state["pending_human_request"])
        submission = HumanInputSubmission.model_validate(state["human_input"])
        interaction = HumanInteraction(
            request_id=request.request_id,
            request_type=request.request_type,
            request=request.model_dump(mode="json"),
            response=submission.response,
            comment=submission.comment,
            actor=submission.actor,
            recorded_at=datetime.now(UTC),
        )
        update: dict[str, Any] = {
            "human_interactions": [
                *state.get("human_interactions", []),
                interaction.model_dump(mode="json"),
            ],
            "pending_human_request": None,
            "current_node": node,
        }
        if request.request_type == HumanRequestType.ADDITIONAL_INFORMATION:
            observations = [
                {
                    "source": "human",
                    "type": field,
                    "value": submission.response[field],
                    "recorded_at": interaction.recorded_at.isoformat(),
                }
                for field in request.requested_fields
                if field != "inspection_image_id"
            ]
            update["human_observations"] = [
                *state.get("human_observations", []), *observations
            ]
            update["human_information_round_count"] = (
                state.get("human_information_round_count", 0) + 1
            )
        elif submission.response.get("decision") == ApprovalDecision.NEEDS_REVISION.value:
            update["action_revision_count"] = state.get("action_revision_count", 0) + 1
        update["events"] = make_events(
            state,
            node,
            "Human interaction recorded separately from machine analysis.",
            payload={"request_type": request.request_type.value},
        )
        update["node_timings"] = self._timing(node, started)
        return update

    def update_context(self, state: AgentState) -> dict[str, Any]:
        node, started = "update_context", perf_counter()
        visual_results = list(state.get("visual_observations", []))
        image_ids = list(state.get("inspection_image_ids", []))
        response = (state.get("human_input") or {}).get("response", {})
        image_id = response.get("inspection_image_id")
        if image_id and self.dependencies.vision_service:
            result = self.dependencies.vision_service.analyze(str(image_id)).model_dump(mode="json")
            if image_id not in image_ids:
                image_ids.append(str(image_id))
            visual_results = [item for item in visual_results if item["image_id"] != image_id]
            visual_results.append(result)
        return {
            "inspection_image_ids": image_ids,
            "visual_observations": visual_results,
            "current_node": node,
            "events": make_events(
                state,
                node,
                "Human observations added to retrieval context without modifying ML output.",
                payload={"observation_count": len(state.get("human_observations", []))},
            ),
            "node_timings": self._timing(node, started),
        }

    def generate_report(self, state: AgentState) -> dict[str, Any]:
        node, started = "generate_report", perf_counter()
        evidence = [EvidenceObject.model_validate(item) for item in state.get("rag_evidence", [])]
        citations = [
            ReportCitation(
                evidence_id=item.evidence_id,
                document_id=item.document_id,
                chunk_id=item.chunk_id,
                title=item.title,
                publisher=item.publisher,
                page=item.page,
                section=item.section,
                official_url=item.official_url or "",
            )
            for item in evidence
        ]
        limitations = [
            "ML confidence is not a calibrated equipment-failure probability.",
            "Recommendations support human decisions and do not control equipment.",
        ]
        if state.get("evidence_status") != "SUFFICIENT":
            limitations.append("The available technical evidence remains incomplete or conflicting.")
        interactions = [
            HumanInteraction.model_validate(item)
            for item in state.get("human_interactions", [])
        ]
        if interactions:
            limitations.append(
                "Human decisions record workflow review and do not establish the diagnosis as fact."
            )
        if interactions and interactions[-1].response.get("decision") == "REJECTED":
            limitations.append("The latest recommended action was rejected by the reviewer.")
        if interactions and interactions[-1].response.get("decision") == "NEEDS_REVISION":
            limitations.append("The reviewer requested revision; no recommendation was approved.")
        report = FinalReport(
            run_id=state["run_id"],
            equipment_id=state["equipment_id"],
            measurement_id=state["measurement_id"],
            demo_scenario=state.get("demo_scenario"),
            analysis_summary=state["analysis_result"],
            diagnosis_candidates=[
                DiagnosisCandidate.model_validate(item)
                for item in state.get("diagnosis_candidates", [])
            ],
            evidence_status=state.get("evidence_status"),
            inspection_plan=[
                InspectionStep.model_validate(item)
                for item in state.get("inspection_plan", [])
            ],
            recommended_actions=[
                RecommendedAction.model_validate(item)
                for item in state.get("recommended_actions", [])
            ],
            human_interactions=interactions,
            limitations=limitations,
            citations=citations,
            historical_context_used=state.get("memory_used_ids", []),
            visual_observations=state.get("visual_observations", []),
            visual_context_used=[
                observation_id
                for item in state.get("diagnosis_candidates", [])
                for observation_id in item.get("supporting_visual_observation_ids", [])
            ],
            version_trace=state["version_trace"],
            created_at=datetime.now(UTC),
        )
        return {
            "final_report": report.model_dump(mode="json"),
            "workflow_status": WorkflowStatus.COMPLETED.value,
            "next_action": "REPORT_COMPLETE",
            "current_node": node,
            "events": make_events(
                state,
                node,
                "Final structured report generated.",
                payload={"citation_count": len(citations)},
                extra_events=[
                    ("report_generated", "Final report generated."),
                    ("workflow_completed", "Workflow completed."),
                ],
            ),
            "node_timings": self._timing(node, started),
        }
