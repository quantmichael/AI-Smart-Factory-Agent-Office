from pathlib import Path

import pytest

from app.rag.embedding import LocalHashingEmbeddingService
from app.rag.ingestion.pipeline import KnowledgeIngestionPipeline
from app.rag.vector_store import ChromaVectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_actual_knowledge_pack_ingestion_is_persistent_and_idempotent(tmp_path) -> None:
    vector_root = tmp_path / "vector_db"
    artifact_root = tmp_path / "rag_artifacts"
    pipeline = KnowledgeIngestionPipeline(
        project_root=PROJECT_ROOT,
        manifest_path=PROJECT_ROOT
        / "knowledge/bearing_v1/manifests/source_manifest.json",
        vector_store=ChromaVectorStore(vector_root, "bearing_v1_test"),
        embedding_service=LocalHashingEmbeddingService(batch_size=32),
        artifact_root=artifact_root,
    )

    first = pipeline.run()
    second = pipeline.run()

    assert first["failed_document_count"] == 0
    assert first["document_count"] == 15
    assert first["ingested_document_count"] == 15
    assert first["indexed_document_count"] == 15
    assert first["chunk_count"] > 0
    assert second["ingested_document_count"] == 0
    assert second["skipped_unchanged_document_count"] == 15
    assert second["vector_store"]["count"] == first["vector_store"]["count"]
    assert (artifact_root / "ingestion_report.json").is_file()
    assert (artifact_root / "sample_chunks.json").is_file()
