"""Vector retrieval boundary with evidence mapping, logging, and deduplication."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections import Counter
from time import perf_counter
from typing import Any

from app.domain.schemas import EvidenceObject
from app.rag.embedding import LocalHashingEmbeddingService
from app.rag.retrieval.filters import build_chroma_where
from app.rag.retrieval.models import (
    RetrievalContext,
    RetrievalPurpose,
    RetrievalQuery,
    RetrievalResult,
    RetrievalStats,
)
from app.rag.retrieval.query_builder import QueryBuilder
from app.rag.vector_store import ChromaVectorStore


logger = logging.getLogger(__name__)


def _chunk_index(chunk_id: str) -> int | None:
    match = re.search(r":c(\d+)$", chunk_id)
    return int(match.group(1)) if match else None


def _overlap(left: str, right: str) -> float:
    a, b = set(left.lower().split()), set(right.lower().split())
    return len(a & b) / max(1, min(len(a), len(b)))


class RetrieverService:
    def __init__(
        self,
        vector_store: ChromaVectorStore,
        embedding_service: LocalHashingEmbeddingService,
        query_builder: QueryBuilder | None = None,
    ) -> None:
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.query_builder = query_builder or QueryBuilder()

    def retrieve_by_purpose(
        self,
        context: RetrievalContext,
        purpose: RetrievalPurpose,
        *,
        top_k: int = 5,
    ) -> RetrievalResult:
        return self.retrieve(self.query_builder.build(context, purpose, top_k=top_k))

    def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        started = perf_counter()
        where = build_chroma_where(query.filters)
        vector = self.embedding_service.embed([query.query_text])[0]
        candidates = self.vector_store.search(
            vector,
            limit=max(query.top_k * 4, query.top_k),
            where=where or None,
        )
        selected: list[dict[str, Any]] = []
        for candidate in candidates:
            metadata = candidate["metadata"]
            adjacent_duplicate = False
            for previous in selected:
                if previous["metadata"]["document_id"] != metadata["document_id"]:
                    continue
                left = _chunk_index(previous["chunk_id"])
                right = _chunk_index(candidate["chunk_id"])
                if (
                    left is not None
                    and right is not None
                    and abs(left - right) <= 1
                    and _overlap(previous["content"], candidate["content"]) >= 0.75
                ):
                    adjacent_duplicate = True
                    break
            if not adjacent_duplicate:
                selected.append(candidate)
            if len(selected) == query.top_k:
                break

        evidence = [self._to_evidence(query, item) for item in selected]
        latency = (perf_counter() - started) * 1000.0
        tiers = Counter(str(item.source_tier) for item in evidence)
        types = Counter(item.document_type for item in evidence)
        scores = [item.retrieval_score or 0.0 for item in evidence]
        stats = RetrievalStats(
            returned=len(evidence),
            latency_ms=latency,
            source_tiers=dict(sorted(tiers.items())),
            document_types=dict(sorted(types.items())),
            retrieved_chunk_ids=[item.chunk_id for item in evidence],
            scores=scores,
        )
        logger.info(
            "rag retrieval %s",
            json.dumps(
                {
                    "query_id": query.query_id,
                    "purpose": query.purpose.value,
                    "query_text": query.query_text,
                    "filters": query.filters,
                    "top_k": query.top_k,
                    "retrieved_chunk_ids": stats.retrieved_chunk_ids,
                    "scores": stats.scores,
                    "latency_ms": latency,
                },
                sort_keys=True,
            ),
        )
        return RetrievalResult(query=query, evidence=evidence, stats=stats)

    @staticmethod
    def _to_evidence(query: RetrievalQuery, item: dict[str, Any]) -> EvidenceObject:
        metadata = dict(item["metadata"])
        roles = metadata.get("rag_roles", "[]")
        if isinstance(roles, str):
            try:
                metadata["rag_roles"] = json.loads(roles)
            except json.JSONDecodeError:
                metadata["rag_roles"] = []
        score = max(-1.0, min(1.0, 1.0 - float(item["distance"])))
        identity = f"{query.query_id}:{item['chunk_id']}"
        evidence_id = "evidence_" + hashlib.sha256(identity.encode()).hexdigest()[:20]
        return EvidenceObject(
            evidence_id=evidence_id,
            query_id=query.query_id,
            purpose=query.purpose.value,
            document_id=metadata["document_id"],
            chunk_id=item["chunk_id"],
            source_id=metadata["source_id"],
            title=metadata["title"],
            publisher=metadata["publisher"],
            document_type=metadata["document_type"],
            source_tier=int(metadata["source_tier"]),
            page=metadata.get("page"),
            section=metadata.get("section"),
            content=item["content"],
            retrieval_score=score,
            official_url=metadata["official_url"],
            metadata=metadata,
        )
