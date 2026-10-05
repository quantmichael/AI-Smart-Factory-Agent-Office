"""Small deterministic hashing-vector index with cosine similarity."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Any


class DeterministicHashingIndex:
    def __init__(self, dimensions: int = 512) -> None:
        self.dimensions = dimensions

    def vectorize(self, text: str) -> dict[int, float]:
        normalized = unicodedata.normalize("NFKC", text).lower()
        words = re.findall(r"[0-9a-z가-힣_]+", normalized)
        compact = re.sub(r"\s+", "", normalized)
        tokens = [f"w:{word}" for word in words]
        for n in (2, 3, 4):
            tokens.extend(f"c{n}:{compact[i:i+n]}" for i in range(max(0, len(compact) - n + 1)))
        vector: dict[int, float] = {}
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] = vector.get(index, 0.0) + sign
        norm = math.sqrt(sum(value * value for value in vector.values()))
        if norm:
            vector = {index: value / norm for index, value in vector.items()}
        return vector

    @staticmethod
    def cosine(left: dict[int, float], right: dict[int, float]) -> float:
        if len(left) > len(right):
            left, right = right, left
        return sum(value * right.get(index, 0.0) for index, value in left.items())

    def build(self, chunks: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
        return {
            chunk["chunk_id"]: {str(index): value for index, value in self.vectorize(chunk["text"]).items()}
            for chunk in chunks
        }

    def search(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        vectors: dict[str, dict[str, float]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        query_vector = self.vectorize(query)
        results = []
        for chunk in chunks:
            stored = {int(index): value for index, value in vectors[chunk["chunk_id"]].items()}
            results.append({**chunk, "retrieval_score": self.cosine(query_vector, stored)})
        return sorted(results, key=lambda item: (-item["retrieval_score"], item["chunk_id"]))[:top_k]

    @staticmethod
    def save(path: str | Path, vectors: dict[str, dict[str, float]]) -> None:
        Path(path).write_text(json.dumps(vectors, ensure_ascii=False, sort_keys=True), encoding="utf-8")

