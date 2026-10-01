from app.rag.retrieval import QueryBuilder, RetrievalPurpose
from rag_helpers import build_test_retriever


def test_search_result_maps_to_canonical_evidence_content(tmp_path) -> None:
    service = build_test_retriever(tmp_path / "vector")
    query = QueryBuilder().build_text_query(
        "inspect raceway lubricant contamination",
        RetrievalPurpose.INSPECTION_ACTION,
        top_k=1,
    )

    evidence = service.retrieve(query).evidence[0]

    assert evidence.query_id == query.query_id
    assert evidence.purpose == "INSPECTION_ACTION"
    assert evidence.content
    assert evidence.page == 12
    assert evidence.section == "Inspection"
    assert "text" not in evidence.model_dump()
