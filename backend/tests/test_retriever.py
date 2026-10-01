from app.rag.retrieval import QueryBuilder, RetrievalPurpose
from rag_helpers import build_test_retriever


def test_retriever_returns_ranked_purpose_filtered_evidence(tmp_path) -> None:
    service = build_test_retriever(tmp_path / "vector")
    query = QueryBuilder().build_text_query(
        "bearing vibration spectrum defect frequency",
        RetrievalPurpose.DIAGNOSTIC_EVIDENCE,
        top_k=2,
    )

    result = service.retrieve(query)

    assert result.stats.returned == 2
    assert result.evidence[0].source_id == "SKF_VIBRATION_DIAGNOSTIC_GUIDE"
    assert result.stats.retrieved_chunk_ids == [item.chunk_id for item in result.evidence]
    assert all(-1 <= item.retrieval_score <= 1 for item in result.evidence)
