#!/usr/bin/env python3
"""Run STEP 03 profiling through PaderbornDatasetAdapter."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.data.adapters.paderborn import PaderbornDatasetAdapter  # noqa: E402
from app.ml.profiling import PaderbornProfiler  # noqa: E402


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=os.getenv("PADERBORN_DATA_ROOT", "data/paderborn"),
    )
    parser.add_argument("--output", default="artifacts/profiling")
    args = parser.parse_args()

    adapter = PaderbornDatasetAdapter(resolve_path(args.root))
    result = PaderbornProfiler(adapter, resolve_path(args.output)).run()
    print(
        "profiling complete: "
        f"measurements={result['dataset_summary']['measurement_count']} "
        f"quality={result['data_quality']['status']} "
        f"window={result['step04_input_spec']['window_duration_sec']}s/"
        f"{result['step04_input_spec']['overlap_percent']}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
