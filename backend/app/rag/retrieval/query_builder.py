"""Deterministic, purpose-specific query construction without diagnosis claims."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.rag.retrieval.models import (
    RetrievalContext,
    RetrievalMode,
    RetrievalPurpose,
    RetrievalQuery,
)


DIAGNOSTIC_DATASET_SOURCES = [
    "PADERBORN_OVERVIEW",
    "PADERBORN_DATASETS_AND_DOWNLOAD",
    "PADERBORN_TEST_RIG",
    "PADERBORN_OPERATING_CONDITIONS",
    "PADERBORN_PUBLICATION",
    "PADERBORN_BENCHMARK_PAPER",
]
EVALUATION_DATASET_SOURCES = DIAGNOSTIC_DATASET_SOURCES + [
    "PADERBORN_DAMAGE_FACT_SHEETS",
    "PADERBORN_MEASUREMENT_LOGS",
    "PADERBORN_DAMAGE",
]
DIAGNOSTIC_SOURCES = [
    "SKF_VIBRATION_DIAGNOSTIC_GUIDE",
    "SKF_BEARING_DAMAGE_FAILURE_ANALYSIS",
    "PADERBORN_DAMAGE",
    "PADERBORN_BENCHMARK_PAPER",
]
INSPECTION_SOURCES = [
    "SKF_BEARING_DAMAGE_FAILURE_ANALYSIS",
    "SKF_VIBRATION_DIAGNOSTIC_GUIDE",
]


def _query_id(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "query_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]


def _purpose_filters(purpose: RetrievalPurpose, mode: RetrievalMode) -> dict[str, Any]:
    if purpose == RetrievalPurpose.DATASET_EVIDENCE:
        sources = (
            EVALUATION_DATASET_SOURCES
            if mode == RetrievalMode.EVALUATION
            else DIAGNOSTIC_DATASET_SOURCES
        )
    elif purpose == RetrievalPurpose.DIAGNOSTIC_EVIDENCE:
        sources = DIAGNOSTIC_SOURCES
    else:
        sources = INSPECTION_SOURCES
    return {
        "knowledge_pack_id": "bearing_v1",
        "component": "bearing",
        "source_tier_lte": 2,
        "source_id_in": sources,
    }


def _merge_filters(base: dict[str, Any], requested: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    allowed_sources = set(base["source_id_in"])
    for key, value in requested.items():
        if key in {"knowledge_pack_id", "component"}:
            if value != base[key]:
                raise ValueError(f"{key} cannot override the knowledge-pack boundary")
        elif key == "source_tier_lte":
            if not isinstance(value, int):
                raise ValueError("source_tier_lte must be an integer")
            merged[key] = min(base[key], value)
        elif key == "source_id":
            if value not in allowed_sources:
                raise ValueError("source_id is outside the purpose/mode boundary")
            merged[key] = value
        elif key == "source_id_in":
            if not isinstance(value, list):
                raise ValueError("source_id_in must be a list")
            intersection = [item for item in value if item in allowed_sources]
            if not intersection:
                raise ValueError("source_id_in is outside the purpose/mode boundary")
            merged[key] = intersection
        else:
            merged[key] = value
    return merged


class QueryBuilder:
    def build(
        self,
        context: RetrievalContext,
        purpose: RetrievalPurpose,
        *,
        top_k: int = 5,
    ) -> RetrievalQuery:
        if purpose == RetrievalPurpose.DATASET_EVIDENCE:
            parts = [
                "Paderborn bearing dataset experimental context test rig operating condition",
                f"analysis status {context.status}",
            ]
            if context.operating_condition:
                parts.append(f"operating condition {context.operating_condition}")
            if context.mode == RetrievalMode.EVALUATION and context.bearing_id:
                parts.append(f"bearing identifier {context.bearing_id} damage fact sheet measurement log")
        elif purpose == RetrievalPurpose.DIAGNOSTIC_EVIDENCE:
            parts = [
                "bearing vibration condition monitoring diagnostic technical evidence",
                f"analysis status {context.status}",
                f"predicted class {context.predicted_class}",
            ]
            parts.extend(f"signal feature {name} {value:.6g}" for name, value in sorted(context.signal_features.items()))
            if context.operating_condition:
                parts.append(f"operating condition {context.operating_condition}")
        else:
            parts = [
                "bearing inspection checks failure analysis maintenance action technical guidance",
                f"analysis status {context.status}",
                f"predicted class {context.predicted_class}",
            ]
            if context.operating_condition:
                parts.append(f"operating condition {context.operating_condition}")
        return self.build_text_query(
            " ".join(parts), purpose, top_k=top_k, mode=context.mode
        )

    def build_text_query(
        self,
        text: str,
        purpose: RetrievalPurpose,
        *,
        top_k: int = 5,
        mode: RetrievalMode = RetrievalMode.DIAGNOSTIC,
        filters: dict[str, Any] | None = None,
    ) -> RetrievalQuery:
        normalized = " ".join(text.split())
        merged = _merge_filters(_purpose_filters(purpose, mode), filters or {})
        payload = {
            "purpose": purpose.value,
            "mode": mode.value,
            "query_text": normalized,
            "filters": merged,
            "top_k": top_k,
        }
        return RetrievalQuery(query_id=_query_id(payload), **payload)
