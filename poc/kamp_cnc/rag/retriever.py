"""Policy-aware retrieval over the isolated kamp_cnc_v1 pack."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from poc.kamp_cnc.knowledge.retrieval import DeterministicHashingIndex
from poc.kamp_cnc.rag.evidence import concise_evidence


class KAMPCNCRetriever:
    def __init__(self, pack_dir: str | Path) -> None:
        self.pack_dir = Path(pack_dir)
        self.manifest = json.loads((self.pack_dir / "manifest.json").read_text(encoding="utf-8"))
        self.chunks = json.loads((self.pack_dir / "chunks.json").read_text(encoding="utf-8"))
        self.vectors = json.loads((self.pack_dir / "index.json").read_text(encoding="utf-8"))
        self.index = DeterministicHashingIndex(self.manifest["retrieval"]["dimensions"])
        self.threshold = self.manifest["retrieval"]["threshold"]

    def retrieve(self, query: str, top_k: int = 3) -> dict[str, Any]:
        policy = self._policy(query)
        if policy is not None:
            return {"status": policy[0], "reason": policy[1], "query": query, "evidence": []}
        results = self.index.search(query, self.chunks, self.vectors, top_k)
        accepted = [result for result in results if result["retrieval_score"] >= self.threshold]
        if not accepted:
            return {
                "status": "INSUFFICIENT_EVIDENCE",
                "reason": f"top score below calibrated threshold {self.threshold}",
                "query": query,
                "evidence": [],
                "top_score": round(results[0]["retrieval_score"], 8) if results else 0.0,
            }
        return {
            "status": "EVIDENCE_FOUND",
            "reason": "Guidebook evidence met the calibrated retrieval threshold",
            "query": query,
            "evidence": [concise_evidence(result) for result in accepted],
        }

    @staticmethod
    def _policy(query: str) -> tuple[str, str] | None:
        lowered = query.lower()
        control_terms = ("자동제어", "자동 제어", "정비 명령", "장비를 정지", "공구를 자동 교체")
        if any(term in lowered for term in control_terms):
            return "OUT_OF_SCOPE", "Guidebook RAG does not issue control or maintenance commands"
        unrelated_terms = ("축구", "주식", "날씨", "급여", "여행", "법률 상담")
        if any(term in lowered for term in unrelated_terms):
            return "OUT_OF_SCOPE", "Query is outside the KAMP CNC Guidebook scope"
        overclaim_terms = ("고장 원인을 확정", "반드시 공구 마모", "정확한 고장 부위", "센서 값만으로 원인")
        if any(term in lowered for term in overclaim_terms):
            return "INSUFFICIENT_EVIDENCE", "Sensor Features and this Guidebook cannot confirm a specific fault cause"
        return None

