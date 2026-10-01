"""Dependency readiness checks used at startup and by the public ready endpoint."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sqlite3
from typing import Any

from app.core.config import Settings, resolve_runtime_path
from app.ml.registry.file_registry import ArtifactModelRegistry


@dataclass(frozen=True, slots=True)
class ReadinessCheck:
    name: str
    ready: bool
    detail: str


def _sqlite_check(name: str, path: Path) -> ReadinessCheck:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
        connection.execute("SELECT 1").fetchone()
        connection.close()
        return ReadinessCheck(name, True, "SQLite connection successful")
    except Exception as exc:
        return ReadinessCheck(name, False, f"{type(exc).__name__}: SQLite unavailable")


def evaluate_readiness(settings: Settings) -> dict[str, Any]:
    dataset = resolve_runtime_path(settings.paderborn_data_root)
    ml_root = resolve_runtime_path(settings.ml_artifact_root)
    vector_db = resolve_runtime_path(settings.vector_db_path)
    knowledge = resolve_runtime_path(settings.knowledge_base_root) / settings.knowledge_pack_id
    checks: list[ReadinessCheck] = []
    dataset_ready = dataset.is_dir() and any(dataset.rglob("*.mat"))
    checks.append(
        ReadinessCheck(
            "dataset",
            dataset_ready,
            "Paderborn measurements available" if dataset_ready else "Paderborn measurements unavailable",
        )
    )
    try:
        model = ArtifactModelRegistry(ml_root, settings.active_ml_model_id).get_active_model()
        model_ready = model.model_path.is_file()
        model_version = str(model.metadata.get("version", "unknown"))
        model_detail = "Active model artifact available" if model_ready else "Active model artifact unavailable"
    except Exception as exc:
        model_ready, model_version, model_detail = False, "unknown", f"{type(exc).__name__}: active model unavailable"
    checks.append(ReadinessCheck("ml_model", model_ready, model_detail))
    manifest_path = knowledge / "manifests" / "source_manifest.json"
    manifest_version = "unknown"
    if manifest_path.is_file():
        try:
            manifest_version = str(json.loads(manifest_path.read_text())["manifest_version"])
        except Exception:
            manifest_version = "invalid"
    knowledge_ready = manifest_path.is_file()
    checks.append(
        ReadinessCheck(
            "knowledge_pack",
            knowledge_ready,
            "Knowledge manifest available" if knowledge_ready else "Knowledge manifest unavailable",
        )
    )
    vector_ready = (vector_db / "chroma.sqlite3").is_file()
    checks.append(
        ReadinessCheck(
            "vector_db",
            vector_ready,
            "Chroma persistence available" if vector_ready else "Chroma persistence unavailable",
        )
    )
    checks.extend([
        _sqlite_check("agent_db", resolve_runtime_path(settings.agent_run_db_path)),
        _sqlite_check("checkpoint_db", resolve_runtime_path(settings.agent_checkpoint_path)),
        _sqlite_check("memory_db", resolve_runtime_path(settings.equipment_memory_db_path)),
        _sqlite_check("vision_db", resolve_runtime_path(settings.inspection_image_db_path)),
    ])
    return {
        "status": "ready" if all(item.ready for item in checks) else "not_ready",
        "checks": [asdict(item) for item in checks],
        "versions": {
            "application": settings.app_version,
            "model_id": settings.active_ml_model_id,
            "model_version": model_version,
            "knowledge_pack_id": settings.knowledge_pack_id,
            "knowledge_manifest_version": manifest_version,
            "workflow": settings.workflow_version,
        },
    }
