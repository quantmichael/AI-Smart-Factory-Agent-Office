from fastapi.testclient import TestClient

from app.core.config import get_settings, resolve_runtime_path
from app.main import app
from app.rag.vector_store import ChromaVectorStore


def test_knowledge_summary_matches_actual_chroma_collection():
    settings = get_settings()
    store = ChromaVectorStore(
        resolve_runtime_path(settings.vector_db_path),
        settings.knowledge_pack_id,
    )
    records = store.get_records()
    document_ids = {record["metadata"]["document_id"] for record in records}

    response = TestClient(app).get("/api/v1/knowledge/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "READY"
    assert body["collection"] == settings.knowledge_pack_id
    assert body["document_count"] == len(document_ids)
    assert body["chunk_count"] == len(records)
    assert body["embedding_count"] == len(records)
    assert body["embedding_method"] == settings.embedding_model
    assert body["embedding_dimension"] == 384
    assert body["distance_metric"] == "cosine"
    assert "persist_directory" not in body


def test_document_list_uses_manifest_metadata_and_actual_chunk_counts():
    client = TestClient(app)
    response = client.get("/api/v1/knowledge/documents")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == len(body["documents"])
    assert body["documents"]
    assert sum(item["chunk_count"] for item in body["documents"]) == client.get(
        "/api/v1/knowledge/summary"
    ).json()["chunk_count"]
    assert all(item["title"] and item["publisher"] for item in body["documents"])
    assert all("local_path" not in item and "sha256" not in item for item in body["documents"])


def test_document_detail_returns_paginated_chunks_without_vectors():
    client = TestClient(app)
    document = client.get("/api/v1/knowledge/documents").json()["documents"][0]

    response = client.get(
        f"/api/v1/knowledge/documents/{document['document_id']}",
        params={"page": 1, "page_size": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["document"]["document_id"] == document["document_id"]
    assert body["chunks"]["page_size"] == 1
    assert body["chunks"]["total"] == document["chunk_count"]
    assert len(body["chunks"]["items"]) == 1
    chunk = body["chunks"]["items"][0]
    assert chunk["chunk_id"]
    assert chunk["content"]
    assert "embedding" not in chunk


def test_missing_knowledge_document_uses_public_not_found_error():
    response = TestClient(app).get("/api/v1/knowledge/documents/not-a-document")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "KNOWLEDGE_DOCUMENT_NOT_FOUND"
