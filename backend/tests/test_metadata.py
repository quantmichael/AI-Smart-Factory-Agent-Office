from app.rag.ingestion.chunking import chunk_document
from app.rag.models import IngestionStatus, KnowledgeDocument, ParsedBlock


def test_chunk_metadata_contains_citation_and_domain_fields() -> None:
    document = KnowledgeDocument(
        document_id="fact-ka01",
        source_id="facts",
        knowledge_pack_id="bearing_v1",
        title="KA01 fact sheet",
        publisher="Paderborn University",
        document_type="damage_fact_sheet",
        source_tier=1,
        rag_roles=["ground_truth"],
        official_url="https://example.test",
        local_path="/tmp/ka01.pdf",
        sha256="b" * 64,
        version="1",
        license="CC BY-NC 4.0",
        license_status="noncommercial-use-with-attribution",
        ingestion_status=IngestionStatus.READY,
        metadata={"bearing_id": "KA01", "fault_type": "artificial"},
    )

    chunk = chunk_document(document, [ParsedBlock(page=1, section="Profile", text="Outer ring damage")])[0]

    assert chunk.document_id == "fact-ka01"
    assert chunk.page == 1
    assert chunk.official_url == "https://example.test"
    assert chunk.bearing_id == "KA01"
    assert chunk.fault_type == "artificial"
    assert chunk.equipment_type == "rotating_machinery"
    assert chunk.component == "bearing"
