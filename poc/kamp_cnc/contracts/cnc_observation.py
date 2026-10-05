"""Contract for a row-level KAMP CNC observation.

The contract intentionally keeps dataset ground truth separate from model output.
It does not perform feature selection or product-level label resolution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


CONTRACT_VERSION = "1.0.0"
ADAPTER_VERSION = "1.0.0"
DATASET_NAME = "정밀가공_품질보증_데이터셋"

STATISTICS = ("max", "mean", "min", "std")
AXES = ("X", "Z1", "Z2", "Z3")

FEATURE_COLUMNS = (
    *(f"SpindleSpeed_{stat}" for stat in STATISTICS),
    *(f"ServoCurrent_{axis}_{stat}" for stat in STATISTICS for axis in AXES),
    *(f"ServoLoad_{axis}_{stat}" for stat in STATISTICS for axis in AXES),
    *(f"SpindleLoad_{stat}" for stat in STATISTICS),
)


@dataclass(frozen=True)
class CNCObservation:
    source: str
    dataset: str
    equipment_type: str
    observation: dict[str, Any]
    process_features: dict[str, Any]
    ground_truth: dict[str, Any]
    data_quality: dict[str, Any]
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

