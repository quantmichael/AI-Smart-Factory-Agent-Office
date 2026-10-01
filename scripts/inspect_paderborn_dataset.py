#!/usr/bin/env python3
"""Inspect and validate Paderborn data without printing or serializing raw arrays."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.data.adapters.paderborn import PaderbornDatasetAdapter  # noqa: E402


def resolve_from_project(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=os.getenv("PADERBORN_DATA_ROOT", "data/paderborn"),
        help="dataset root; defaults to PADERBORN_DATA_ROOT or data/paderborn",
    )
    parser.add_argument(
        "--inspection-output",
        default="artifacts/data/paderborn_inspection.json",
    )
    parser.add_argument(
        "--validation-output",
        default="artifacts/data/paderborn_validation.json",
    )
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()

    adapter = PaderbornDatasetAdapter(resolve_from_project(args.root))
    inspection = adapter.inspection_summary()
    inspection["inspection_timestamp"] = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )
    write_json(resolve_from_project(args.inspection_output), inspection)
    print(
        f"inspection: measurements={inspection['mat_file_count']} "
        f"bearings={len(inspection['bearing_ids'])}"
    )

    if not args.skip_validation:
        validation = adapter.validate()
        payload = validation.model_dump(mode="json")
        payload["validation_timestamp"] = datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )
        write_json(resolve_from_project(args.validation_output), payload)
        print(
            f"validation: status={validation.status} "
            f"invalid={validation.invalid_measurement_count} "
            f"seconds={validation.validation_seconds:.3f}"
        )
        return 0 if validation.status == "pass" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
