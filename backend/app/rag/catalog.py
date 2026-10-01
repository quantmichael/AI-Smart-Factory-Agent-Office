"""Read-only catalog views over the manifest-approved Chroma collection."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from pydantic import Field

from app.domain.schemas.common import StrictSchema
from app.rag.embedding import LocalHashingEmbeddingService
from app.rag.ingestion.manifest import load_manifest
from app.rag.models import KnowledgeDocument
from app.rag.vector_store import ChromaVectorStore


class KnowledgeSummary(StrictSchema):
    knowledge_pack: str
    knowledge_version: str
    vector_store: str
    collection: str
    document_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    embedding_count: int = Field(ge=0)
    embedding_method: str
    embedding_dimension: int = Field(ge=1)
    distance_metric: str
    status: str


class KnowledgeDocumentSummary(StrictSchema):
    document_id: str
    title: str
    publisher: str
    document_type: str
    source: str
    version: str
    license: str
    license_status: str
    official_url: str | None = None
    indexed_pages: list[int] = Field(default_factory=list)
    chunk_count: int = Field(ge=0)


class KnowledgeDocumentList(StrictSchema):
    documents: list[KnowledgeDocumentSummary]
    total: int = Field(ge=0)


class KnowledgeChunkView(StrictSchema):
    chunk_id: str
    page: int | None = None
    section: str | None = None
    content: str


class KnowledgeChunkPage(StrictSchema):
    items: list[KnowledgeChunkView]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class KnowledgeDocumentDetail(StrictSchema):
    document: KnowledgeDocumentSummary
    chunks: KnowledgeChunkPage


class KnowledgeDocumentNotFoundError(LookupError):
    pass


def _chunk_sort_key(record: dict[str, Any]) -> tuple[int, str, str]:
    metadata = record["metadata"]
    page = metadata.get("page")
    return (int(page) if page is not None else 0, str(metadata.get("section") or ""), record["chunk_id"])


class KnowledgeCatalogService:
    """Join canonical source metadata with the records actually stored in Chroma."""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        manifest_path: Path,
        project_root: Path,
        embedding_service: LocalHashingEmbeddingService,
    ) -> None:
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        payload, documents, _ = load_manifest(manifest_path, project_root)
        self.knowledge_version = str(payload["manifest_version"])
        self.documents = {document.document_id: document for document in documents}

    def _records(self, document_id: str | None = None) -> list[dict[str, Any]]:
        return self.vector_store.get_records(document_id)

    def summary(self) -> KnowledgeSummary:
        records = self._records()
        document_ids = {str(record["metadata"]["document_id"]) for record in records}
        collection_metadata = self.vector_store.collection.metadata or {}
        model_names = {
            str(record["metadata"].get("embedding_model"))
            for record in records
            if record["metadata"].get("embedding_model")
        }
        method = (
            next(iter(model_names))
            if len(model_names) == 1
            else self.embedding_service.config.model
        )
        return KnowledgeSummary(
            knowledge_pack=self.vector_store.collection_name,
            knowledge_version=self.knowledge_version,
            vector_store="Chroma",
            collection=self.vector_store.collection_name,
            document_count=len(document_ids),
            chunk_count=len(records),
            embedding_count=len(records),
            embedding_method=method,
            embedding_dimension=self.embedding_service.config.dimension,
            distance_metric=str(collection_metadata.get("hnsw:space", "cosine")),
            status="READY",
        )

    def list_documents(self) -> KnowledgeDocumentList:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for record in self._records():
            grouped.setdefault(str(record["metadata"]["document_id"]), []).append(record)
        documents = [
            self._document_summary(document_id, records)
            for document_id, records in grouped.items()
        ]
        documents.sort(key=lambda item: (item.publisher.lower(), item.title.lower(), item.document_id))
        return KnowledgeDocumentList(documents=documents, total=len(documents))

    def document_detail(
        self,
        document_id: str,
        *,
        page: int,
        page_size: int,
    ) -> KnowledgeDocumentDetail:
        records = sorted(self._records(document_id), key=_chunk_sort_key)
        if not records:
            raise KnowledgeDocumentNotFoundError(document_id)
        total = len(records)
        start = (page - 1) * page_size
        selected = records[start : start + page_size]
        chunks = [
            KnowledgeChunkView(
                chunk_id=record["chunk_id"],
                page=record["metadata"].get("page"),
                section=record["metadata"].get("section"),
                content=record["content"],
            )
            for record in selected
        ]
        return KnowledgeDocumentDetail(
            document=self._document_summary(document_id, records),
            chunks=KnowledgeChunkPage(
                items=chunks,
                page=page,
                page_size=page_size,
                total=total,
                total_pages=math.ceil(total / page_size),
            ),
        )

    def _document_summary(
        self,
        document_id: str,
        records: list[dict[str, Any]],
    ) -> KnowledgeDocumentSummary:
        manifest_document = self.documents.get(document_id)
        metadata = records[0]["metadata"]
        pages = sorted(
            {
                int(record["metadata"]["page"])
                for record in records
                if record["metadata"].get("page") is not None
            }
        )
        return KnowledgeDocumentSummary(
            document_id=document_id,
            title=(manifest_document.title if manifest_document else str(metadata.get("title", document_id))),
            publisher=(manifest_document.publisher if manifest_document else str(metadata.get("publisher", ""))),
            document_type=(manifest_document.document_type if manifest_document else str(metadata.get("document_type", ""))),
            source=(manifest_document.source_id if manifest_document else str(metadata.get("source_id", ""))),
            version=(manifest_document.version if manifest_document else str(metadata.get("document_version", ""))),
            license=(manifest_document.license if manifest_document else ""),
            license_status=(manifest_document.license_status if manifest_document else str(metadata.get("license_status", ""))),
            official_url=(manifest_document.official_url if manifest_document else metadata.get("official_url")) or None,
            indexed_pages=pages,
            chunk_count=len(records),
        )
