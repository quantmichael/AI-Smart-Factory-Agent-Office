"""Section/page-aware chunking with stable deterministic identifiers."""

from __future__ import annotations

import hashlib
import re

from app.rag.models import KnowledgeChunk, KnowledgeDocument, ParsedBlock


CHUNKING_VERSION = "section-word-v1"
MAX_TOKENS = 800
OVERLAP_TOKENS = 100


def approximate_tokens(text: str) -> list[str]:
    return re.findall(r"\S+", text)


def _chunk_id(document_id: str, page: int | None, section: str | None, index: int) -> str:
    section_hash = hashlib.sha1((section or "unsectioned").encode("utf-8")).hexdigest()[:8]
    return f"{document_id}:p{page or 0:04d}:s{section_hash}:c{index:04d}"


def chunk_document(
    document: KnowledgeDocument,
    blocks: list[ParsedBlock],
    *,
    max_tokens: int = MAX_TOKENS,
    overlap_tokens: int = OVERLAP_TOKENS,
) -> list[KnowledgeChunk]:
    if max_tokens < 1 or not 0 <= overlap_tokens < max_tokens:
        raise ValueError("invalid chunk size/overlap")
    grouped_blocks: list[ParsedBlock] = []
    for block in blocks:
        if (
            grouped_blocks
            and grouped_blocks[-1].page == block.page
            and grouped_blocks[-1].section == block.section
        ):
            previous = grouped_blocks[-1]
            grouped_blocks[-1] = ParsedBlock(
                page=previous.page,
                section=previous.section,
                text=f"{previous.text}\n\n{block.text}",
                metadata={
                    **previous.metadata,
                    "combined_structural_blocks": int(
                        previous.metadata.get("combined_structural_blocks", 1)
                    )
                    + 1,
                },
            )
        else:
            grouped_blocks.append(block)
    chunks: list[KnowledgeChunk] = []
    index = 0
    for block in grouped_blocks:
        tokens = approximate_tokens(block.text)
        if not tokens:
            continue
        start = 0
        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            content = " ".join(tokens[start:end]).strip()
            if content:
                chunks.append(
                    KnowledgeChunk(
                        knowledge_pack_id=document.knowledge_pack_id,
                        document_id=document.document_id,
                        chunk_id=_chunk_id(document.document_id, block.page, block.section, index),
                        source_id=document.source_id,
                        title=document.title,
                        publisher=document.publisher,
                        document_type=document.document_type,
                        source_tier=document.source_tier,
                        rag_roles=document.rag_roles,
                        page=block.page,
                        section=block.section,
                        content=content,
                        fault_type=document.metadata.get("fault_type"),
                        bearing_id=document.metadata.get("bearing_id"),
                        operating_condition=document.metadata.get("operating_condition"),
                        official_url=document.official_url,
                        sha256=document.sha256,
                        document_version=document.version,
                        license_status=document.license_status,
                        metadata={
                            **block.metadata,
                            "chunking_version": CHUNKING_VERSION,
                            "token_count_approx": end - start,
                        },
                    )
                )
                index += 1
            if end == len(tokens):
                break
            start = end - overlap_tokens
    ids = [chunk.chunk_id for chunk in chunks]
    if not chunks or len(ids) != len(set(ids)):
        raise ValueError(f"invalid chunks generated for {document.document_id}")
    return chunks
