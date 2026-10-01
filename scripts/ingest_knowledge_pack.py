#!/usr/bin/env python3
"""Validate and ingest a local knowledge pack into Chroma."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.rag.embedding import LocalHashingEmbeddingService  # noqa: E402
from app.rag.ingestion.pipeline import KnowledgeIngestionPipeline  # noqa: E402
from app.rag.vector_store import ChromaVectorStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", choices=["bearing_v1"], default="bearing_v1")
    parser.add_argument("--source-id")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--vector-root", default="artifacts/vector_db")
    parser.add_argument("--artifact-root", default="artifacts/rag/bearing_v1")
    args = parser.parse_args()
    pipeline = KnowledgeIngestionPipeline(
        project_root=PROJECT_ROOT,
        manifest_path=PROJECT_ROOT / f"knowledge/{args.pack}/manifests/source_manifest.json",
        vector_store=ChromaVectorStore(PROJECT_ROOT / args.vector_root, args.pack),
        embedding_service=LocalHashingEmbeddingService(),
        artifact_root=PROJECT_ROOT / args.artifact_root,
    )
    report = pipeline.run(source_id=args.source_id, force=args.force, dry_run=args.dry_run)
    print(
        f"pack={args.pack} sources={report['source_count']} documents={report['document_count']} "
        f"chunks={report['chunk_count']} ingested={report['ingested_document_count']} "
        f"skipped={report['skipped_unchanged_document_count']} failed={report['failed_document_count']} "
        f"dry_run={args.dry_run}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
