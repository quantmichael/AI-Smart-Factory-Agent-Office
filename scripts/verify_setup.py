"""Verify that the prepared local MVP environment is reproducible and ready."""

from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.core.config import Settings  # noqa: E402
from app.core.readiness import evaluate_readiness  # noqa: E402


def main() -> None:
    readiness = evaluate_readiness(Settings())
    files = {
        "environment_template": (PROJECT_ROOT / ".env.example").is_file(),
        "backend_requirements": (PROJECT_ROOT / "backend" / "requirements.txt").is_file(),
        "frontend_lockfile": (PROJECT_ROOT / "frontend" / "package-lock.json").is_file(),
        "demo_registry": (PROJECT_ROOT / "config" / "demo_scenarios.json").is_file(),
        "interface_freeze": (PROJECT_ROOT / "config" / "interface_freeze_mvp_rc1.json").is_file(),
        "dataset_manifest": (PROJECT_ROOT / "data" / "paderborn" / "metadata" / "dataset_files.json").is_file(),
        "knowledge_manifest": (PROJECT_ROOT / "knowledge" / "bearing_v1" / "manifests" / "source_manifest.json").is_file(),
    }
    result = {
        "status": "pass" if readiness["status"] == "ready" and all(files.values()) and sys.version_info >= (3, 11) else "fail",
        "python": sys.version.split()[0],
        "files": files,
        "readiness": readiness,
        "scope": "prepared local environment; does not claim a fresh-machine network install",
    }
    output = PROJECT_ROOT / "artifacts" / "e2e" / "setup_verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, ensure_ascii=False))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
