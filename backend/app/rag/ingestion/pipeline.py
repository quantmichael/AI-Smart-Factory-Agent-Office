"""End-to-end, manifest-gated knowledge pack ingestion."""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from app.rag.embedding import LocalHashingEmbeddingService
from app.rag.ingestion.chunking import CHUNKING_VERSION, chunk_document
from app.rag.ingestion.manifest import load_manifest
from app.rag.ingestion.parsers import parse_html, parse_pdf
from app.rag.models import IngestionStatus, KnowledgeChunk, KnowledgeDocument
from app.rag.vector_store import ChromaVectorStore


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _parse(document: KnowledgeDocument):
    path = Path(document.local_path)
    if path.suffix.lower() == ".pdf":
        return parse_pdf(path), "PDF"
    if path.suffix.lower() in {".html", ".htm"}:
        return parse_html(path), "HTML"
    raise ValueError(f"unsupported document suffix: {path.suffix}")


class KnowledgeIngestionPipeline:
    def __init__(
        self,
        *,
        project_root: Path | str,
        manifest_path: Path | str,
        vector_store: ChromaVectorStore,
        embedding_service: LocalHashingEmbeddingService,
        artifact_root: Path | str,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.manifest_path = Path(manifest_path)
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.artifact_root = Path(artifact_root)

    def run(
        self,
        *,
        source_id: str | None = None,
        force: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        manifest, documents, source_statuses = load_manifest(
            self.manifest_path, self.project_root
        )
        if source_id:
            if source_id not in {item["source_id"] for item in source_statuses}:
                raise ValueError(f"source_id not present in manifest: {source_id}")
            documents = [document for document in documents if document.source_id == source_id]
        document_rows: list[dict[str, Any]] = []
        chunk_rows: list[dict[str, Any]] = []
        all_chunks: list[KnowledgeChunk] = []
        sample_chunks: list[dict[str, Any]] = []
        failures: list[dict[str, str]] = []
        skipped = 0
        ingested = 0
        embedding_config = asdict(self.embedding_service.config)

        for document in documents:
            try:
                blocks, parser = _parse(document)
                chunks = chunk_document(document, blocks)
                current = (
                    not force
                    and not dry_run
                    and self.vector_store.document_is_current(
                        document.document_id,
                        document.sha256,
                        self.embedding_service.config.version,
                        {chunk.chunk_id for chunk in chunks},
                    )
                )
                if current:
                    status = IngestionStatus.SKIPPED
                    skipped += 1
                elif dry_run:
                    status = IngestionStatus.READY
                else:
                    vectors = self.embedding_service.embed([chunk.content for chunk in chunks])
                    self.vector_store.delete_document(document.document_id)
                    self.vector_store.add_chunks(chunks, vectors, embedding_config)
                    status = IngestionStatus.INGESTED
                    ingested += 1
                all_chunks.extend(chunks)
                token_counts = [int(chunk.metadata["token_count_approx"]) for chunk in chunks]
                document_rows.append(
                    {
                        "document_id": document.document_id,
                        "source_id": document.source_id,
                        "title": document.title,
                        "document_type": document.document_type,
                        "source_tier": document.source_tier,
                        "parser": parser,
                        "page_or_block_count": len(blocks),
                        "chunk_count": len(chunks),
                        "status": status.value,
                        "sha256": document.sha256,
                        "local_path": document.local_path,
                    }
                )
                chunk_rows.append(
                    {
                        "document_id": document.document_id,
                        "chunk_count": len(chunks),
                        "min_tokens_approx": min(token_counts),
                        "max_tokens_approx": max(token_counts),
                        "average_tokens_approx": mean(token_counts),
                        "pages_with_chunks": len({chunk.page for chunk in chunks if chunk.page}),
                    }
                )
                review_candidates = [
                    item for item in chunks if item.page is None or item.page >= 5
                ] or chunks
                first = max(
                    review_candidates,
                    key=lambda item: int(item.metadata["token_count_approx"]),
                )
                sample_chunks.append(
                    {
                        "document_id": first.document_id,
                        "chunk_id": first.chunk_id,
                        "page": first.page,
                        "section": first.section,
                        "source_id": first.source_id,
                        "title": first.title,
                        "publisher": first.publisher,
                        "document_type": first.document_type,
                        "source_tier": first.source_tier,
                        "rag_roles": first.rag_roles,
                        "official_url": first.official_url,
                        "bearing_id": first.bearing_id,
                        "fault_type": first.fault_type,
                        "sha256": first.sha256,
                        "license_status": first.license_status,
                        "metadata": first.metadata,
                        "content": first.content,
                    }
                )
            except Exception as exc:
                failures.append(
                    {
                        "document_id": document.document_id,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                document_rows.append(
                    {
                        "document_id": document.document_id,
                        "source_id": document.source_id,
                        "title": document.title,
                        "document_type": document.document_type,
                        "source_tier": document.source_tier,
                        "parser": "",
                        "page_or_block_count": 0,
                        "chunk_count": 0,
                        "status": IngestionStatus.FAILED.value,
                        "sha256": document.sha256,
                        "local_path": document.local_path,
                    }
                )

        if failures and not dry_run:
            raise RuntimeError(f"ingestion failed for {len(failures)} document(s): {failures}")
        for item in source_statuses:
            item["manifest_validation_status"] = item["status"]
            if not dry_run and item["status"] == IngestionStatus.READY.value:
                item["status"] = IngestionStatus.INGESTED.value
        source_counts = Counter(item["status"] for item in source_statuses)
        chunks_by_type = Counter(chunk.document_type for chunk in all_chunks)
        chunks_by_tier = Counter(str(chunk.source_tier) for chunk in all_chunks)
        chunks_by_role = Counter(role for chunk in all_chunks for role in chunk.rag_roles)
        token_counts = [int(chunk.metadata["token_count_approx"]) for chunk in all_chunks]
        report = {
            "knowledge_pack": "bearing_v1",
            "manifest_version": manifest["manifest_version"],
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "dry_run": dry_run,
            "source_count": len(source_statuses),
            "source_status_counts": dict(sorted(source_counts.items())),
            "ready_source_count": sum(
                item["manifest_validation_status"] == "READY" for item in source_statuses
            ),
            "ingested_source_count": sum(
                item["status"] == "INGESTED" for item in source_statuses
            ),
            "document_count": len(documents),
            "ingested_document_count": ingested,
            "skipped_unchanged_document_count": skipped,
            "failed_document_count": len(failures),
            "chunk_count": len(all_chunks),
            "average_chunk_tokens_approx": mean(token_counts) if token_counts else 0,
            "chunks_by_document_type": dict(sorted(chunks_by_type.items())),
            "chunks_by_source_tier": dict(sorted(chunks_by_tier.items())),
            "chunks_by_rag_role": dict(sorted(chunks_by_role.items())),
            "embedding": embedding_config,
            "chunking": {
                "strategy": CHUNKING_VERSION,
                "max_tokens": 800,
                "overlap_tokens": 100,
            },
            "vector_store": (
                {
                    "status": "not_modified_dry_run",
                    "type": "Chroma",
                    "collection": self.vector_store.collection_name,
                    "persist_directory": str(self.vector_store.persist_directory),
                }
                if dry_run
                else self.vector_store.get_stats()
            ),
            "source_statuses": source_statuses,
            "failures": failures,
            "warnings": [
                item["warning"] for item in source_statuses if item.get("warning")
            ],
        }
        report["indexed_document_count"] = (
            0 if dry_run else report["vector_store"]["document_count"]
        )
        self._write_artifacts(report, document_rows, chunk_rows, sample_chunks)
        return report

    def _write_artifacts(
        self,
        report: dict[str, Any],
        documents: list[dict[str, Any]],
        chunks: list[dict[str, Any]],
        samples: list[dict[str, Any]],
    ) -> None:
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        (self.artifact_root / "ingestion_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (self.artifact_root / "sample_chunks.json").write_text(
            json.dumps(samples, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        _write_csv(
            self.artifact_root / "document_stats.csv",
            documents,
            [
                "document_id", "source_id", "title", "document_type", "source_tier",
                "parser", "page_or_block_count", "chunk_count", "status", "sha256",
                "local_path",
            ],
        )
        _write_csv(
            self.artifact_root / "chunk_stats.csv",
            chunks,
            [
                "document_id", "chunk_count", "min_tokens_approx", "max_tokens_approx",
                "average_tokens_approx", "pages_with_chunks",
            ],
        )
        lines = [
            "# bearing_v1 Ingestion Report",
            "",
            f"- Generated: `{report['generated_at']}`",
            f"- Sources: {report['source_count']} ({report['ready_source_count']} ready)",
            f"- Documents: {report['document_count']}",
            f"- Documents currently indexed: {report['indexed_document_count']}",
            f"- Ingested this run: {report['ingested_document_count']}",
            f"- Skipped unchanged: {report['skipped_unchanged_document_count']}",
            f"- Failed: {report['failed_document_count']}",
            f"- Chunks: {report['chunk_count']}",
            f"- Average approximate tokens: {report['average_chunk_tokens_approx']:.1f}",
            f"- Embedding: `{report['embedding']['provider']}/{report['embedding']['model']}`",
            f"- Vector collection: `{report['vector_store']['collection']}`",
            "",
            "## Warnings",
            "",
        ]
        lines.extend(f"- {warning}" for warning in report["warnings"])
        lines.extend(
            [
                "",
                "## Review",
                "",
                "Inspect `sample_chunks.json` for one citation-ready chunk per document.",
                "Page is omitted for HTML and preserved as a one-based number for PDF chunks.",
                "",
            ]
        )
        (self.artifact_root / "INGESTION_REPORT.md").write_text(
            "\n".join(lines), encoding="utf-8"
        )
