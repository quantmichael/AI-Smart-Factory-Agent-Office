"""Deterministic Hit@K, Recall@K, MRR, and empty-result evaluation."""

from __future__ import annotations

from statistics import mean
from typing import Any

from app.rag.retrieval import QueryBuilder, RetrievalMode, RetrievalPurpose, RetrieverService


def _relevant(item: dict[str, Any], case: dict[str, Any]) -> bool:
    sources = set(case.get("expected_source_ids", []))
    types = set(case.get("expected_document_types", []))
    if sources:
        return item.get("source_id") in sources
    return bool(types and item.get("document_type") in types)


def evaluate_cases(
    service: RetrieverService,
    cases: list[dict[str, Any]],
    *,
    ks: tuple[int, ...] = (3, 5),
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    maximum = max(ks)
    results: list[dict[str, Any]] = []
    answerable = [case for case in cases if case.get("answerable", True)]
    for case in cases:
        query = QueryBuilder().build_text_query(
            case["question"],
            RetrievalPurpose(case["purpose"]),
            top_k=maximum,
            mode=RetrievalMode(case.get("mode", "DIAGNOSTIC")),
            filters=case.get("filters", {}),
        )
        response = service.retrieve(query)
        evidence = [item.model_dump(mode="json") for item in response.evidence]
        rank = next(
            (index for index, item in enumerate(evidence, start=1) if _relevant(item, case)),
            None,
        )
        per_k: dict[str, Any] = {}
        expected_sources = set(case.get("expected_source_ids", []))
        for k in ks:
            top = evidence[:k]
            retrieved_sources = {item.get("source_id") for item in top}
            hit = any(_relevant(item, case) for item in top)
            recall = (
                len(expected_sources & retrieved_sources) / len(expected_sources)
                if expected_sources
                else float(hit)
            )
            per_k[str(k)] = {"hit": float(hit), "recall": recall}
        results.append(
            {
                "case": case,
                "query": query.model_dump(mode="json"),
                "evidence": evidence,
                "stats": response.stats.model_dump(mode="json"),
                "first_relevant_rank": rank,
                "metrics": per_k,
            }
        )

    answerable_results = [result for result in results if result["case"].get("answerable", True)]
    metrics: dict[str, Any] = {
        "case_count": len(cases),
        "answerable_case_count": len(answerable),
        "unanswerable_case_count": len(cases) - len(answerable),
        "empty_result_rate": mean(not result["evidence"] for result in results),
        "mrr": mean(
            1 / result["first_relevant_rank"] if result["first_relevant_rank"] else 0
            for result in answerable_results
        ),
    }
    for k in ks:
        metrics[f"hit_at_{k}"] = mean(
            result["metrics"][str(k)]["hit"] for result in answerable_results
        )
        metrics[f"recall_at_{k}"] = mean(
            result["metrics"][str(k)]["recall"] for result in answerable_results
        )
    metrics["expected_source_hit_rate_at_5"] = metrics["hit_at_5"]
    metrics["failure_case_ids_at_5"] = [
        result["case"]["case_id"]
        for result in answerable_results
        if not result["metrics"]["5"]["hit"]
    ]
    metrics["unanswerable_nonempty_case_ids"] = [
        result["case"]["case_id"]
        for result in results
        if not result["case"].get("answerable", True) and result["evidence"]
    ]
    return metrics, results
