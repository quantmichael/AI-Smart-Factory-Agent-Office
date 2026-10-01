from app.rag.ingestion.chunking import chunk_document
from app.rag.models import IngestionStatus, KnowledgeDocument, ParsedBlock


def document() -> KnowledgeDocument:
    return KnowledgeDocument(
        document_id="doc-1",
        source_id="source-1",
        knowledge_pack_id="bearing_v1",
        title="Guide",
        publisher="Publisher",
        document_type="inspection_guide",
        source_tier=2,
        rag_roles=["inspection"],
        official_url="https://example.test/guide",
        local_path="/tmp/guide.pdf",
        sha256="a" * 64,
        version="1",
        license="test",
        license_status="test-only",
        ingestion_status=IngestionStatus.READY,
    )


def test_chunking_is_stable_unique_and_preserves_citation_metadata() -> None:
    blocks = [ParsedBlock(page=3, section="Inspection", text=" ".join(f"w{i}" for i in range(25)))]

    first = chunk_document(document(), blocks, max_tokens=10, overlap_tokens=2)
    second = chunk_document(document(), blocks, max_tokens=10, overlap_tokens=2)

    assert [item.chunk_id for item in first] == [item.chunk_id for item in second]
    assert len(first) == 3
    assert len({item.chunk_id for item in first}) == 3
    assert all(item.page == 3 and item.section == "Inspection" for item in first)
    assert all(item.content for item in first)
    assert first[0].content.split()[-2:] == first[1].content.split()[:2]
