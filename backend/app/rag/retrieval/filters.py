"""Allowlisted conversion from public filters to Chroma predicates."""

from __future__ import annotations

from typing import Any


EQUALITY_FIELDS = {
    "knowledge_pack_id",
    "component",
    "source_id",
    "publisher",
    "document_type",
    "bearing_id",
    "fault_type",
}


def build_chroma_where(filters: dict[str, Any]) -> dict[str, Any]:
    clauses: list[dict[str, Any]] = []
    for key, value in filters.items():
        if key in EQUALITY_FIELDS:
            if not isinstance(value, (str, int, float, bool)):
                raise ValueError(f"filter {key} must be a scalar")
            clauses.append({key: {"$eq": value}})
        elif key == "source_tier_lte":
            if not isinstance(value, int) or not 1 <= value <= 4:
                raise ValueError("source_tier_lte must be an integer from 1 to 4")
            clauses.append({"source_tier": {"$lte": value}})
        elif key.endswith("_in") and key.removesuffix("_in") in EQUALITY_FIELDS:
            field = key.removesuffix("_in")
            if not isinstance(value, list) or not value or not all(
                isinstance(item, (str, int, float, bool)) for item in value
            ):
                raise ValueError(f"filter {key} must be a non-empty scalar list")
            clauses.append({field: {"$in": value}})
        else:
            raise ValueError(f"unsupported metadata filter: {key}")
    if not clauses:
        return {}
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}
