"""Run the isolated KAMP CNC adapter against the full supplied CSV."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from poc.kamp_cnc.adapter import AdapterValidationError, KAMPCNCAdapter
from poc.kamp_cnc.contracts import ADAPTER_VERSION, CONTRACT_VERSION, FEATURE_COLUMNS


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "raw" / "정밀가공_품질보증_데이터셋.csv"


def flatten_feature_count(observation: dict[str, Any]) -> int:
    features = observation["process_features"]
    return (
        len(features["spindle_speed"])
        + sum(len(v) for v in features["servo_current"].values())
        + sum(len(v) for v in features["servo_load"].values())
        + len(features["spindle_load"])
    )


def flatten_features(observation: dict[str, Any]) -> dict[str, float]:
    process = observation["process_features"]
    flattened = {f"SpindleSpeed_{stat}": value for stat, value in process["spindle_speed"].items()}
    for axis, statistics in process["servo_current"].items():
        flattened.update({f"ServoCurrent_{axis}_{stat}": value for stat, value in statistics.items()})
    for axis, statistics in process["servo_load"].items():
        flattened.update({f"ServoLoad_{axis}_{stat}": value for stat, value in statistics.items()})
    flattened.update({f"SpindleLoad_{stat}": value for stat, value in process["spindle_load"].items()})
    return flattened


def run() -> tuple[dict[str, Any], dict[str, Any]]:
    adapter = KAMPCNCAdapter()
    rows = adapter.read_csv(CSV_PATH)
    pair_index = adapter.build_pair_index(rows)
    observations = []
    failures = []
    for row_index, row in enumerate(rows):
        try:
            observations.append(adapter.adapt_row(row, row_index, pair_index[row_index]).to_dict())
        except AdapterValidationError as exc:
            failures.append({"row_index": row_index, "code": exc.code, "message": str(exc)})

    labels = Counter(obs["ground_truth"]["status"] for obs in observations)
    sample_ids = [obs["observation"]["sample_id"] for obs in observations]
    feature_value_mismatches = sum(
        float(rows[obs["observation"]["row_index"]][column]) != value
        for obs in observations
        for column, value in flatten_features(obs).items()
    )
    paired = [obs for obs in observations if obs["data_quality"]["paired_serial"]]
    unpaired_pass = next(obs for obs in observations if obs["ground_truth"]["status"] == "PASS" and not obs["data_quality"]["paired_serial"])
    first_fail = next(obs for obs in observations if obs["ground_truth"]["status"] == "FAIL")
    paired_pass = next(obs for obs in paired if obs["ground_truth"]["status"] == "PASS")
    paired_fail = next(obs for obs in paired if obs["ground_truth"]["status"] == "FAIL")

    summary = {
        "phase": "K1-B",
        "contract": "CNCObservation",
        "contract_version": CONTRACT_VERSION,
        "adapter": "KAMPCNCAdapter",
        "adapter_version": ADAPTER_VERSION,
        "input_csv": str(CSV_PATH.relative_to(ROOT.parent.parent)),
        "input_rows": len(rows),
        "converted": len(observations),
        "PASS": labels["PASS"],
        "FAIL": labels["FAIL"],
        "paired_observation_rows": len(paired),
        "paired_serial_groups": len({obs["observation"]["serial_no"] for obs in paired}),
        "validation_failures": len(failures),
        "failure_details": failures,
        "unique_sample_ids": len(set(sample_ids)),
        "duplicate_sample_ids": len(sample_ids) - len(set(sample_ids)),
        "feature_columns_expected": len(FEATURE_COLUMNS),
        "feature_values_per_observation": sorted({flatten_feature_count(obs) for obs in observations}),
        "feature_value_mismatches": feature_value_mismatches,
        "ground_truth": {
            "mapping": {"0": "PASS", "1": "FAIL"},
            "source_type": "dataset_ground_truth",
            "prediction": False,
        },
        "verdict": "PASS" if len(observations) == len(rows) and not failures and len(sample_ids) == len(set(sample_ids)) and feature_value_mismatches == 0 else "FAIL",
    }
    examples = {
        "general_PASS": unpaired_pass,
        "general_FAIL": {
            "unpaired_FAIL_available_in_source": False,
            "reason": "All 99 FAIL rows in the supplied CSV belong to paired observations.",
            "observation": first_fail,
        },
        "paired_PASS": paired_pass,
        "paired_FAIL": paired_fail,
    }
    return summary, examples


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", choices=("summary", "examples", "all"), default="all")
    args = parser.parse_args()
    summary, examples = run()
    payload: Any = summary if args.output == "summary" else examples if args.output == "examples" else {"summary": summary, "examples": examples}
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
