import numpy as np

from app.rag.embedding import LocalHashingEmbeddingService
from app.rag.ingestion.chunking import chunk_document
from app.rag.models import IngestionStatus, KnowledgeDocument, ParsedBlock
from app.rag.vector_store import ChromaVectorStore


def _chunks():
    document = KnowledgeDocument(
        document_id="doc-vector",
        source_id="source-vector",
        knowledge_pack_id="bearing_v1",
        title="Bearing Guide",
        publisher="Publisher",
        document_type="vibration_diagnostic_guide",
        source_tier=2,
        rag_roles=["vibration_diagnosis"],
        official_url="https://example.test",
        local_path="/tmp/guide.pdf",
        sha256="c" * 64,
        version="1",
        license="test",
        license_status="test",
        ingestion_status=IngestionStatus.READY,
    )
    return chunk_document(
        document,
        [
            ParsedBlock(page=1, section="Vibration", text="bearing vibration spectrum diagnosis"),
            ParsedBlock(page=2, section="Lubrication", text="lubrication inspection procedure"),
        ],
    )


def test_vector_store_add_search_filter_upsert_delete_and_reload(tmp_path) -> None:
    embedding = LocalHashingEmbeddingService(batch_size=2)
    chunks = _chunks()
    vectors = embedding.embed([item.content for item in chunks])
    config = {
        "provider": embedding.config.provider,
        "model": embedding.config.model,
        "version": embedding.config.version,
    }
    store = ChromaVectorStore(tmp_path, "test_collection")
    store.add_chunks(chunks, vectors, config)
    store.add_chunks(chunks, vectors, config)

    assert store.get_stats()["count"] == 2
    assert store.document_is_current(
        "doc-vector", "c" * 64, embedding.config.version, {item.chunk_id for item in chunks}
    )
    query = embedding.embed(["vibration spectrum"])[0]
    results = store.search(query, where={"document_type": "vibration_diagnostic_guide"})
    assert results
    assert results[0]["metadata"]["document_id"] == "doc-vector"

    reloaded = ChromaVectorStore(tmp_path, "test_collection")
    assert reloaded.get_stats()["count"] == 2
    reloaded.delete_document("doc-vector")
    assert reloaded.get_stats()["count"] == 0
