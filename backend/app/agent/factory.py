"""Runtime construction that reuses STEP 05 and STEP 07 services."""

from __future__ import annotations

from pathlib import Path

from app.agent.nodes import AgentDependencies
from app.agent.actions import ConservativeActionPlanner
from app.agent.policies import ActionPolicy
from app.agent.reasoning import ConservativeEvidenceReasoner, DeterministicEvidenceVerifier
from app.agent.service import AgentWorkflowService
from app.data.adapters.paderborn import PaderbornDatasetAdapter
from app.rag.embedding import LocalHashingEmbeddingService
from app.rag.retrieval import RetrieverService
from app.rag.vector_store import ChromaVectorStore
from app.services.analysis import build_analysis_service
from app.ml.registry import ArtifactModelRegistry
from app.memory import EquipmentMemoryRepository, EquipmentMemoryService
from app.vision import InspectionImageRepository, InspectionImageService, LocalQualityVisionAnalyzer


def build_agent_service(
    *,
    dataset_root: Path,
    ml_artifact_root: Path,
    active_model_id: str,
    vector_db_path: Path,
    checkpoint_path: Path,
    memory_db_path: Path | None = None,
    vision_db_path: Path | None = None,
    vision_upload_root: Path | None = None,
    vision_enabled: bool = True,
    vision_model: str = "pillow-quality-observer-v1",
    max_image_size_mb: int = 8,
    max_image_dimension: int = 4096,
    application_version: str = "0.1.0",
    knowledge_pack_id: str = "bearing_v1",
    knowledge_manifest_version: str = "unknown",
    workflow_version: str = "diagnosis_core_v1",
    max_retrieval_retries: int = 2,
    max_human_information_rounds: int = 2,
    max_action_revision_rounds: int = 1,
    diagnosis_reasoner=None,
    evidence_verifier=None,
    action_planner=None,
) -> AgentWorkflowService:
    if vision_model != LocalQualityVisionAnalyzer.model_id:
        raise ValueError(f"unsupported configured vision model: {vision_model}")
    model_metadata = ArtifactModelRegistry(ml_artifact_root, active_model_id).get_active_model().metadata
    analysis = build_analysis_service(
        dataset_root,
        ml_artifact_root,
        active_model_id,
        PaderbornDatasetAdapter,
    )
    retriever = RetrieverService(
        ChromaVectorStore(vector_db_path, "bearing_v1"),
        LocalHashingEmbeddingService(),
    )
    return AgentWorkflowService(
        AgentDependencies(
            analysis_service=analysis,
            retriever=retriever,
            diagnosis_reasoner=diagnosis_reasoner or ConservativeEvidenceReasoner(),
            evidence_verifier=evidence_verifier or DeterministicEvidenceVerifier(),
            action_planner=action_planner or ConservativeActionPlanner(),
            action_policy=ActionPolicy(),
            max_retrieval_retries=max_retrieval_retries,
            max_human_information_rounds=max_human_information_rounds,
            max_action_revision_rounds=max_action_revision_rounds,
            memory_service=(
                EquipmentMemoryService(EquipmentMemoryRepository(memory_db_path))
                if memory_db_path is not None else None
            ),
            vision_service=(
                InspectionImageService(
                    InspectionImageRepository(vision_db_path),
                    LocalQualityVisionAnalyzer(),
                    vision_upload_root,
                    max_size_mb=max_image_size_mb,
                    max_dimension=max_image_dimension,
                    enabled=vision_enabled,
                )
                if vision_db_path is not None and vision_upload_root is not None
                else None
            ),
            version_trace={
                "application_version": application_version,
                "model_id": active_model_id,
                "model_version": str(model_metadata.get("version", "unknown")),
                "knowledge_pack_id": knowledge_pack_id,
                "knowledge_manifest_version": knowledge_manifest_version,
                "workflow_version": workflow_version,
            },
        ),
        checkpoint_path,
    )
