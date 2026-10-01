#!/usr/bin/env python3
"""Call the real STEP 05 API in-process and write a bounded smoke artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.api.v1.analysis import get_analysis_service  # noqa: E402
from app.data.adapters.paderborn import PaderbornDatasetAdapter  # noqa: E402
from app.main import app  # noqa: E402
from app.services.analysis import build_analysis_service  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="data/paderborn")
    parser.add_argument("--artifacts", default="artifacts/ml")
    parser.add_argument("--output", default="artifacts/api/step05_smoke_result.json")
    args = parser.parse_args()
    resolve = lambda value: Path(value) if Path(value).is_absolute() else PROJECT_ROOT / value
    service = build_analysis_service(
        resolve(args.root),
        resolve(args.artifacts),
        "bearing_rf_binary_v1",
        PaderbornDatasetAdapter,
    )
    summaries = service.adapter.list_measurements()
    selected = [
        next(item for item in summaries if item.ground_truth.state == state)
        for state in ("healthy", "damaged")
    ]
    app.dependency_overrides[get_analysis_service] = lambda: service
    results = []
    try:
        client = TestClient(app)
        for summary in selected:
            started = perf_counter()
            response = client.post(
                "/api/v1/analysis",
                json={"measurement_id": summary.measurement_id},
            )
            elapsed_ms = (perf_counter() - started) * 1000.0
            response.raise_for_status()
            body = response.json()
            results.append(
                {
                    "ground_truth": summary.ground_truth.state,
                    "request": {"measurement_id": summary.measurement_id},
                    "http_status": response.status_code,
                    "api_elapsed_ms": elapsed_ms,
                    "response": body,
                }
            )
    finally:
        app.dependency_overrides.clear()
    output = resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"results": results}, indent=2) + "\n", encoding="utf-8")
    for item in results:
        print(
            item["ground_truth"],
            item["response"]["predicted_class"],
            item["response"]["status"],
            f"{item['api_elapsed_ms']:.2f}ms",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
