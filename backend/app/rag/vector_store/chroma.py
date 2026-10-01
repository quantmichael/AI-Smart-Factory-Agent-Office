"""Chroma-backed persistent vector collection for one knowledge pack."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chromadb
import numpy as np

from app.rag.models import KnowledgeChunk


def _metadata(chunk: KnowledgeChunk, embedding_config: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {
        "knowledge_pack_id": chunk.knowledge_pack_id,
        "document_id": chunk.document_id,
        "chunk_id": chunk.chunk_id,
        "source_id": chunk.source_id,
        "title": chunk.title,
        "publisher": chunk.publisher,
        "document_type": chunk.document_type,
        "source_tier": chunk.source_tier,
        "rag_roles": json.dumps(chunk.rag_roles),
        "equipment_type": chunk.equipment_type,
        "component": chunk.component,
        "official_url": chunk.official_url,
        "sha256": chunk.sha256,
        "document_version": chunk.document_version,
        "license_status": chunk.license_status,
        "embedding_provider": embedding_config["provider"],
        "embedding_model": embedding_config["model"],
        "embedding_version": embedding_config["version"],
        "embedded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    optional = {
        "page": chunk.page,
        "section": chunk.section,
        "fault_type": chunk.fault_type,
        "bearing_id": chunk.bearing_id,
        "operating_condition": chunk.operating_condition,
    }
    values.update({key: value for key, value in optional.items() if value is not None})
    return values


class ChromaVectorStore:
    def __init__(self, persist_directory: Path | str, collection_name: str):
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self.persist_directory))
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine", "knowledge_pack_id": self.collection_name},
            )
        return self._collection

    def add_chunks(
        self,
        chunks: list[KnowledgeChunk],
        embeddings: np.ndarray,
        embedding_config: dict[str, Any],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunk and embedding counts differ")
        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.content for chunk in chunks],
            embeddings=embeddings.tolist(),
            metadatas=[_metadata(chunk, embedding_config) for chunk in chunks],
        )

    def search(
        self,
        query_embedding: np.ndarray,
        *,
        limit: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        count = self.collection.count()
        if count == 0:
            return []
        result = self.collection.query(
            query_embeddings=[query_embedding.astype(float).tolist()],
            n_results=min(limit, count),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        if not result["ids"]:
            return []
        return [
            {
                "chunk_id": chunk_id,
                "content": document,
                "metadata": metadata,
                "distance": distance,
            }
            for chunk_id, document, metadata, distance in zip(
                result["ids"][0],
                result["documents"][0],
                result["metadatas"][0],
                result["distances"][0],
                strict=True,
            )
        ]

    def get_chunk(self, chunk_id: str) -> dict[str, Any] | None:
        result = self.collection.get(ids=[chunk_id], include=["documents", "metadatas"])
        if not result["ids"]:
            return None
        return {
            "chunk_id": result["ids"][0],
            "content": result["documents"][0],
            "metadata": result["metadatas"][0],
        }

    def get_records(self, document_id: str | None = None) -> list[dict[str, Any]]:
        """Return stored text and metadata without exposing embedding vectors."""

        where = {"document_id": document_id} if document_id else None
        result = self.collection.get(
            where=where,
            include=["documents", "metadatas"],
        )
        return [
            {
                "chunk_id": chunk_id,
                "content": document,
                "metadata": metadata,
            }
            for chunk_id, document, metadata in zip(
                result["ids"],
                result["documents"],
                result["metadatas"],
                strict=True,
            )
        ]

    def delete_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})

    def document_is_current(
        self,
        document_id: str,
        sha256: str,
        embedding_version: str,
        chunk_ids: set[str],
    ) -> bool:
        result = self.collection.get(where={"document_id": document_id}, include=["metadatas"])
        if set(result["ids"]) != chunk_ids or not result["ids"]:
            return False
        return all(
            metadata.get("sha256") == sha256
            and metadata.get("embedding_version") == embedding_version
            for metadata in result["metadatas"]
        )

    def get_stats(self) -> dict[str, Any]:
        result = self.collection.get(include=["metadatas"])
        return {
            "type": "Chroma",
            "collection": self.collection_name,
            "count": self.collection.count(),
            "document_count": len(
                {metadata["document_id"] for metadata in result["metadatas"]}
            ),
            "persist_directory": str(self.persist_directory),
        }
