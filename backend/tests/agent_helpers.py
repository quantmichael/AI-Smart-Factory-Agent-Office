from pathlib import Path

from app.agent.nodes import AgentDependencies
from app.agent.actions import ConservativeActionPlanner
from app.agent.schemas import (
    ActionPriority,
    ActionType,
    EvidenceStatus,
    VerificationResult,
)
from app.agent.policies import ActionPolicy
from app.agent.reasoning import ConservativeEvidenceReasoner, DeterministicEvidenceVerifier
from app.agent.service import AgentWorkflowService
from app.data.models import GroundTruth, MeasurementSummary, OperatingCondition
from app.domain.schemas import AnalysisResult, EvidenceObject
from app.rag.retrieval import RetrievalResult, RetrievalStats


class FakeAdapter:
    def __init__(self) -> None:
        self.summary = MeasurementSummary(
            measurement_id="fake:measurement:1",
            equipment_id="fake-rig",
            source="test",
            bearing_id="KA01",
            operating_condition=OperatingCondition(code="N15_M07_F10"),
            run_index=1,
            ground_truth=GroundTruth(
                state="damaged",
                fault_type="must-not-leak",
                damage_location="must-not-leak",
            ),
            source_reference="fixture",
        )

    def get_metadata(self, measurement_id: str):
        if measurement_id != self.summary.measurement_id:
            raise KeyError(measurement_id)
        return self.summary


class FakeAnalysisService:
    def __init__(self, status: str = "abnormal") -> None:
        self.adapter = FakeAdapter()
        self.status = status
        self.calls = 0

    def analyze(self, measurement_id: str) -> AnalysisResult:
        self.calls += 1
        return AnalysisResult(
            analysis_id="analysis-fake",
            measurement_id=measurement_id,
            model_id="model-fake",
            status=self.status,
            predicted_class="damaged" if self.status == "abnormal" else "healthy",
            confidence=0.8,
            signal_features={"rms": 1.2},
            metadata={
                "bearing_id": "KA01",
                "operating_condition": "N15_M07_F10",
            },
        )


class FakeRetriever:
    def __init__(self) -> None:
        self.calls = 0

    def retrieve(self, query):
        self.calls += 1
        suffix = query.purpose.value.lower()
        evidence = EvidenceObject(
            evidence_id=f"evidence-{query.query_id}",
            query_id=query.query_id,
            purpose=query.purpose.value,
            document_id=f"document-{suffix}",
            chunk_id=f"chunk-{suffix}",
            source_id="SKF_BEARING_DAMAGE_FAILURE_ANALYSIS",
            title="Bearing guide",
            publisher="SKF",
            document_type="failure_analysis_guide",
            source_tier=2,
            page=10,
            section="Inspection",
            content="Bearing technical evidence for diagnosis and inspection.",
            retrieval_score=0.5,
            official_url="https://example.test/guide",
        )
        return RetrievalResult(
            query=query,
            evidence=[evidence],
            stats=RetrievalStats(
                returned=1,
                latency_ms=1,
                source_tiers={"2": 1},
                document_types={"failure_analysis_guide": 1},
                retrieved_chunk_ids=[evidence.chunk_id],
                scores=[0.5],
            ),
        )


def build_fake_agent_service(
    checkpoint: Path,
    *,
    status: str = "abnormal",
    verifier=None,
    planner=None,
    max_retries: int = 2,
    max_human_rounds: int = 2,
    max_revision_rounds: int = 1,
):
    analysis = FakeAnalysisService(status)
    retriever = FakeRetriever()
    service = AgentWorkflowService(
        AgentDependencies(
            analysis_service=analysis,
            retriever=retriever,
            diagnosis_reasoner=ConservativeEvidenceReasoner(),
            evidence_verifier=verifier or DeterministicEvidenceVerifier(),
            action_planner=planner or ConservativeActionPlanner(),
            action_policy=ActionPolicy(),
            max_retrieval_retries=max_retries,
            max_human_information_rounds=max_human_rounds,
            max_action_revision_rounds=max_revision_rounds,
        ),
        checkpoint,
    )
    return service, analysis, retriever


class ShutdownReviewPlanner(ConservativeActionPlanner):
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
                summary="Controlled additional-information request.",
            )
        return self.delegate.verify(candidates, evidence)
