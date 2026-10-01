from app.rag.retrieval import QueryBuilder, RetrievalPurpose
from rag_helpers import build_test_retriever


def test_citation_metadata_resolves_to_the_stored_chunk(tmp_path) -> None:
    service = build_test_retriever(tmp_path / "vector")
    query = QueryBuilder().build_text_query(
        "bearing vibration spectrum",
        RetrievalPurpose.DIAGNOSTIC_EVIDENCE,
        top_k=1,
    )
    evidence = service.retrieve(query).evidence[0]
    stored = service.vector_store.get_chunk(evidence.chunk_id)

    assert stored is not None
    assert stored["content"] == evidence.content
    assert stored["metadata"]["document_id"] == evidence.document_id
    assert stored["metadata"]["official_url"] == evidence.official_url
    assert evidence.title and evidence.publisher and evidence.source_id
