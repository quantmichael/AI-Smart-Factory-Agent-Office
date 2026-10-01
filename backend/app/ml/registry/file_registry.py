"""Discover trained models from versioned artifact metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.ml.inference import ModelNotFoundError


@dataclass(frozen=True, slots=True)
class ModelRegistryEntry:
    model_id: str
    artifact_directory: Path
    model_path: Path
    metadata: dict[str, Any]


class ArtifactModelRegistry:
    """Small file registry; no external MLOps platform is required."""

    def __init__(self, root: Path | str, active_model_id: str | None = None):
        self.root = Path(root)
        self.active_model_id = active_model_id

    def entries(self) -> tuple[ModelRegistryEntry, ...]:
        discovered: list[ModelRegistryEntry] = []
        for metadata_path in sorted(self.root.glob("*/metadata.json")):
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            model_path = metadata_path.parent / "model.joblib"
            if model_path.is_file() and metadata.get("model_id"):
                discovered.append(
                    ModelRegistryEntry(
                        model_id=str(metadata["model_id"]),
                        artifact_directory=metadata_path.parent,
                        model_path=model_path,
                        metadata=metadata,
                    )
                )
        return tuple(discovered)

    def get(self, model_id: str) -> ModelRegistryEntry:
        matches = [entry for entry in self.entries() if entry.model_id == model_id]
        if not matches:
            raise ModelNotFoundError(f"model_id not found in artifact registry: {model_id}")
        if len(matches) > 1:
            raise ValueError(f"duplicate model_id in artifact registry: {model_id}")
        return matches[0]

    def get_model(self, model_id: str) -> ModelRegistryEntry:
        return self.get(model_id)

    def get_active_model(self) -> ModelRegistryEntry:
        if self.active_model_id:
            return self.get(self.active_model_id)
        entries = self.entries()
        if len(entries) != 1:
            raise ModelNotFoundError("active model is not configured unambiguously")
        return entries[0]
