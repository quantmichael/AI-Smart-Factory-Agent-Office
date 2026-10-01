#!/usr/bin/env python3
"""Evaluate the STEP 07 vector-only retrieval baseline and write artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.rag.embedding import LocalHashingEmbeddingService  # noqa: E402
from app.rag.evaluation import evaluate_cases  # noqa: E402
from app.rag.retrieval import RetrieverService  # noqa: E402
from app.rag.vector_store import ChromaVectorStore  # noqa: E402


def main() -> int:
    cases_path = PROJECT_ROOT / "backend/app/rag/evaluation/evaluation_cases.json"
    artifact_root = PROJECT_ROOT / "artifacts/rag/bearing_v1/retrieval"
    artifact_root.mkdir(parents=True, exist_ok=True)
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    service = RetrieverService(
        ChromaVectorStore(PROJECT_ROOT / "artifacts/vector_db", "bearing_v1"),
        LocalHashingEmbeddingService(),
    )
    metrics, results = evaluate_cases(service, cases)
    (artifact_root / "evaluation_cases.json").write_text(
        json.dumps(cases, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (artifact_root / "retrieval_results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (artifact_root / "retrieval_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    failures = metrics["failure_case_ids_at_5"]
    by_id = {item["case"]["case_id"]: item for item in results}
    examples = []
    for purpose in ("DATASET_EVIDENCE", "DIAGNOSTIC_EVIDENCE", "INSPECTION_ACTION"):
        example = next(item for item in results if item["case"]["purpose"] == purpose)
        examples.append(
            f"- `{purpose}`: {example['query']['query_text']}"
        )
    failure_lines = []
    for case_id in failures:
        item = by_id[case_id]
        expected = ", ".join(item["case"].get("expected_source_ids", [])) or "none"
        returned = ", ".join(
            dict.fromkeys(evidence["source_id"] for evidence in item["evidence"])
        ) or "none"
        failure_lines.append(
            f"- `{case_id}`: expected `{expected}`; top-5 returned `{returned}`."
        )
    report = [
        "# bearing_v1 Retrieval Report",
        "",
        "- Knowledge pack: `bearing_v1`",
        "- Retriever: vector similarity with metadata filtering",
        "- Embedding: `local/sklearn-hashing-vectorizer-v1`",
        "- Collection: `bearing_v1`",
        f"- Evaluation cases: {metrics['case_count']}",
        f"- Hit@3: {metrics['hit_at_3']:.4f}",
        f"- Hit@5: {metrics['hit_at_5']:.4f}",
        f"- Recall@3: {metrics['recall_at_3']:.4f}",
        f"- Recall@5: {metrics['recall_at_5']:.4f}",
        f"- MRR: {metrics['mrr']:.4f}",
        f"- Empty result rate: {metrics['empty_result_rate']:.4f}",
        "",
        "## Metadata filters",
        "",
        "All searches enforce `knowledge_pack_id=bearing_v1`, `component=bearing`, ",
        "source tier 1-2, and purpose-specific source allowlists. Bearing-specific ",
        "ground-truth sources are available only in EVALUATION mode.",
        "",
        "## Failure cases",
        "",
        *(failure_lines or ["- None"]),
        "",
        "The vector-only baseline also returned low-score candidates for the unanswerable ",
        "PLC-control case. Scores and the non-empty result are preserved for a later ",
        "evidence-sufficiency threshold; no candidate is promoted to an answer here.",
        "",
        "## Query examples",
        "",
        *examples,
        "",
        "## Recommended improvements",
        "",
        "- Review failed queries, parsing, chunking, and filter scope before changing embeddings.",
        "- Consider a relevance threshold for unanswerable questions in a later verification step.",
        "- Evaluate keyword/hybrid retrieval for exact bearing IDs and fault terminology after this baseline.",
        "",
        "Retrieval scores are ranking signals, not probabilities that evidence is true.",
    ]
    (artifact_root / "RETRIEVAL_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
