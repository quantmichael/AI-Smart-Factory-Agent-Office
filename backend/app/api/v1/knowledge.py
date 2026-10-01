"""Read-only endpoints for the manifest-approved knowledge index."""

from __future__ import annotations

from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.exceptions import APIError
from app.core.config import get_settings, resolve_runtime_path
from app.rag.catalog import (
    KnowledgeCatalogService,
    KnowledgeDocumentDetail,
    KnowledgeDocumentList,
    KnowledgeDocumentNotFoundError,
    KnowledgeSummary,
)
from app.rag.embedding import LocalHashingEmbeddingService
from app.rag.retrieval import (
    KnowledgeSearchRequest,
    QueryBuilder,
    RetrievalResult,
    RetrieverService,
)
from app.rag.vector_store import ChromaVectorStore


router = APIRouter(prefix="/knowledge", tags=["knowledge"])
_service: RetrieverService | None = None
_service_lock = Lock()
_catalog_service: KnowledgeCatalogService | None = None
_catalog_service_lock = Lock()


def get_retriever_service() -> RetrieverService:
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                settings = get_settings()
                if settings.embedding_provider != "local":
                    raise RuntimeError("STEP 07 supports only the configured local embedding provider")
                embedding = LocalHashingEmbeddingService(settings.embedding_batch_size)
                if settings.embedding_model != embedding.config.model:
                    raise RuntimeError("configured embedding model does not match the indexed model")
                _service = RetrieverService(
                    ChromaVectorStore(resolve_runtime_path(settings.vector_db_path), settings.knowledge_pack_id),
                    embedding,
                )
    return _service


def get_knowledge_catalog_service() -> KnowledgeCatalogService:
    global _catalog_service
    if _catalog_service is None:
        with _catalog_service_lock:
            if _catalog_service is None:
                settings = get_settings()
                embedding = LocalHashingEmbeddingService(settings.embedding_batch_size)
                knowledge_root = resolve_runtime_path(settings.knowledge_base_root)
                _catalog_service = KnowledgeCatalogService(
                    ChromaVectorStore(
                        resolve_runtime_path(settings.vector_db_path),
                        settings.knowledge_pack_id,
                    ),
                    knowledge_root / settings.knowledge_pack_id / "manifests" / "source_manifest.json",
                    knowledge_root.parent,
                    embedding,
                )
    return _catalog_service


@router.get("/summary", response_model=KnowledgeSummary)
def get_knowledge_summary(
    service: KnowledgeCatalogService = Depends(get_knowledge_catalog_service),
) -> KnowledgeSummary:
    try:
        return service.summary()
    except Exception as exc:
        raise APIError(503, "KNOWLEDGE_BASE_UNAVAILABLE", "Knowledge Base를 조회할 수 없습니다.") from exc


@router.get("/documents", response_model=KnowledgeDocumentList)
def list_knowledge_documents(
    service: KnowledgeCatalogService = Depends(get_knowledge_catalog_service),
) -> KnowledgeDocumentList:
    try:
        return service.list_documents()
    except Exception as exc:
        raise APIError(503, "KNOWLEDGE_BASE_UNAVAILABLE", "기술문서 목록을 조회할 수 없습니다.") from exc


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentDetail)
def get_knowledge_document(
    document_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    service: KnowledgeCatalogService = Depends(get_knowledge_catalog_service),
) -> KnowledgeDocumentDetail:
    try:
        return service.document_detail(document_id, page=page, page_size=page_size)
    except KnowledgeDocumentNotFoundError as exc:
        raise APIError(404, "KNOWLEDGE_DOCUMENT_NOT_FOUND", "기술문서를 찾을 수 없습니다.") from exc
    except Exception as exc:
        raise APIError(503, "KNOWLEDGE_BASE_UNAVAILABLE", "기술문서를 조회할 수 없습니다.") from exc


@router.post(
    "/search",
    response_model=RetrievalResult,
    summary="Search citation-ready bearing evidence",
)
def search_knowledge(
    request: KnowledgeSearchRequest,
    service: RetrieverService = Depends(get_retriever_service),
) -> RetrievalResult:
    try:
        query = QueryBuilder().build_text_query(
            request.query,
            request.purpose,
            top_k=request.top_k,
            mode=request.mode,
            filters=request.filters,
        )
        return service.retrieve(query)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
