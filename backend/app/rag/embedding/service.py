"""Local deterministic embeddings with no external model download."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer


@dataclass(frozen=True, slots=True)
class EmbeddingConfig:
    provider: str = "local"
    model: str = "sklearn-hashing-vectorizer-v1"
    version: str = "word-bigram-384-v1"
    dimension: int = 384
    batch_size: int = 64


class LocalHashingEmbeddingService:
    """Stateless word/bigram hashing vectors suitable for a local MVP index."""

    def __init__(self, batch_size: int = 64):
        self.config = EmbeddingConfig(batch_size=batch_size)
        self._vectorizer = HashingVectorizer(
            n_features=self.config.dimension,
            alternate_sign=False,
            norm="l2",
            analyzer="word",
            ngram_range=(1, 2),
            lowercase=True,
        )

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts or any(not text.strip() for text in texts):
            raise ValueError("embedding input must contain non-empty text")
        batches = []
        for start in range(0, len(texts), self.config.batch_size):
            batch = texts[start : start + self.config.batch_size]
            last_error: Exception | None = None
            for _ in range(2):
                try:
                    batches.append(self._vectorizer.transform(batch).toarray().astype(np.float32))
                    last_error = None
                    break
                except Exception as exc:  # pragma: no cover - defensive provider boundary
                    last_error = exc
            if last_error is not None:
                raise RuntimeError("embedding batch failed after bounded retry") from last_error
        vectors = np.vstack(batches)
        if vectors.shape != (len(texts), self.config.dimension) or not np.isfinite(vectors).all():
            raise RuntimeError("embedding provider returned invalid vectors")
        return vectors
