"""Evidence result helpers."""

from __future__ import annotations

from typing import Any


def concise_evidence(result: dict[str, Any], max_chars: int = 650) -> dict[str, Any]:
    text = result["text"]
    excerpt = text if len(text) <= max_chars else f"{text[:max_chars].rstrip()}..."
    return {
        "source": result["provider"],
        "source_id": result["source_id"],
        "document_title": result["document_title"],
        "page": result["page"],
        "section": result["section"],
        "chunk_id": result["chunk_id"],
        "retrieval_score": round(result["retrieval_score"], 8),
        "excerpt": excerpt,
    }
