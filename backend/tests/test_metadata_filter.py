import pytest

from app.rag.retrieval.filters import build_chroma_where


def test_metadata_filters_are_allowlisted_and_combined() -> None:
    where = build_chroma_where(
        {
            "knowledge_pack_id": "bearing_v1",
            "source_tier_lte": 2,
            "source_id_in": ["A", "B"],
        }
    )

    assert where == {
        "$and": [
            {"knowledge_pack_id": {"$eq": "bearing_v1"}},
            {"source_tier": {"$lte": 2}},
            {"source_id": {"$in": ["A", "B"]}},
        ]
    }


def test_metadata_filter_rejects_unknown_or_invalid_values() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        build_chroma_where({"arbitrary": "value"})
    with pytest.raises(ValueError, match="source_tier_lte"):
        build_chroma_where({"source_tier_lte": 9})
