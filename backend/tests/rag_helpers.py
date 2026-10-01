from pathlib import Path

from app.rag.embedding import LocalHashingEmbeddingService
from app.rag.ingestion.chunking import chunk_document
from app.rag.models import IngestionStatus, KnowledgeDocument, ParsedBlock
from app.rag.retrieval import RetrieverService
from app.rag.vector_store import ChromaVectorStore


def build_test_retriever(path: Path) -> RetrieverService:
    documents = [
        KnowledgeDocument(
            document_id="skf-vibration",
            source_id="SKF_VIBRATION_DIAGNOSTIC_GUIDE",
            knowledge_pack_id="bearing_v1",
            title="Vibration Guide",
            publisher="SKF",
            document_type="vibration_diagnostic_guide",
            source_tier=2,
            rag_roles=["vibration_diagnosis"],
            official_url="https://example.test/vibration",
            local_path="/tmp/vibration.pdf",
            sha256="a" * 64,
            version="1",
            license="test",
            license_status="local-test",
            ingestion_status=IngestionStatus.READY,
        ),
        KnowledgeDocument(
            document_id="skf-failure",
            source_id="SKF_BEARING_DAMAGE_FAILURE_ANALYSIS",
            knowledge_pack_id="bearing_v1",
            title="Failure Guide",
            publisher="SKF",
            document_type="failure_analysis_guide",
            source_tier=2,
            rag_roles=["failure_analysis", "inspection"],
            official_url="https://example.test/failure",
            local_path="/tmp/failure.pdf",
            sha256="b" * 64,
            version="1",
            license="test",
            license_status="local-test",
            ingestion_status=IngestionStatus.READY,
        ),
    ]
    chunks = []
    chunks.extend(
        chunk_document(
            documents[0],
            [ParsedBlock(page=7, section="Spectrum", text="bearing vibration spectrum defect frequency diagnosis")],
        )
    )
    chunks.extend(
        chunk_document(
            documents[1],
            [ParsedBlock(page=12, section="Inspection", text="inspect bearing raceway lubricant contamination and damage")],
        )
    )
    embedding = LocalHashingEmbeddingService()
    store = ChromaVectorStore(path, "bearing_v1")
    store.add_chunks(
        chunks,
        embedding.embed([chunk.content for chunk in chunks]),
        {
            "provider": embedding.config.provider,
            "model": embedding.config.model,
            "version": embedding.config.version,
        },
    )
    return RetrieverService(store, embedding)
