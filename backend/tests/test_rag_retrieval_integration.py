from pathlib import Path
import json

import pytest
from fastapi.testclient import TestClient

from app.api.v1.knowledge import get_retriever_service
from app.main import app
from app.rag.embedding import LocalHashingEmbeddingService
from app.rag.retrieval import QueryBuilder, RetrievalPurpose, RetrieverService
from app.rag.vector_store import ChromaVectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _service() -> RetrieverService:
    return RetrieverService(
        ChromaVectorStore(PROJECT_ROOT / "artifacts/vector_db", "bearing_v1"),
        LocalHashingEmbeddingService(),
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    ("text", "purpose"),
    [
        ("Paderborn bearing test rig operating conditions", RetrievalPurpose.DATASET_EVIDENCE),
        ("bearing vibration spectrum defect frequency", RetrievalPurpose.DIAGNOSTIC_EVIDENCE),
        ("bearing spalling fatigue failure", RetrievalPurpose.DIAGNOSTIC_EVIDENCE),
        ("bearing raceway lubricant inspection", RetrievalPurpose.INSPECTION_ACTION),
    ],
)
def test_real_bearing_index_returns_traceable_chunks(text, purpose) -> None:
    service = _service()
    result = service.retrieve(QueryBuilder().build_text_query(text, purpose, top_k=3))
    manifest = json.loads(
        (PROJECT_ROOT / "knowledge/bearing_v1/manifests/source_manifest.json").read_text()
    )
    official_urls = {
        item["source_id"]: item["official_url"] for item in manifest["sources"]
    }

    assert result.evidence
    for evidence in result.evidence:
        stored = service.vector_store.get_chunk(evidence.chunk_id)
        assert stored is not None
        assert stored["content"] == evidence.content
        assert evidence.official_url == stored["metadata"]["official_url"]
        assert evidence.official_url == official_urls[evidence.source_id]
        assert evidence.page is None or evidence.page >= 1


@pytest.mark.integration
def test_knowledge_search_api_returns_citation_ready_evidence() -> None:
    app.dependency_overrides[get_retriever_service] = _service
    try:
        response = TestClient(app).post(
            "/api/v1/knowledge/search",
            json={
                "query": "bearing vibration defect frequency",
                "purpose": "DIAGNOSTIC_EVIDENCE",
                "top_k": 3,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["evidence"]
    assert body["evidence"][0]["content"]
    assert body["evidence"][0]["official_url"]
    assert body["stats"]["returned"] <= 3
