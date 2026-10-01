#!/usr/bin/env python3
"""Train and evaluate the fixed STEP 04 Random Forest baseline."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.data.adapters.paderborn import PaderbornDatasetAdapter  # noqa: E402
from app.ml.dataset import load_input_spec  # noqa: E402
from app.ml.training.baseline import run_baseline  # noqa: E402


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=os.getenv("PADERBORN_DATA_ROOT", "data/paderborn"))
    parser.add_argument("--input-spec", default="artifacts/profiling/step04_input_spec.json")
    parser.add_argument("--output", default="artifacts/ml/baseline_v1")
    args = parser.parse_args()
    adapter = PaderbornDatasetAdapter(resolve_path(args.root))
    result = run_baseline(
        adapter,
        load_input_spec(resolve_path(args.input_spec)),
        resolve_path(args.output),
    )
    metrics = result["metrics"]["measurement_level"]
    print(
        "baseline complete: "
        f"measurements={len(result['split']['train_measurements'])}+"
        f"{len(result['split']['test_measurements'])} "
        f"accuracy={metrics['accuracy']:.4f} f1={metrics['f1']:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
