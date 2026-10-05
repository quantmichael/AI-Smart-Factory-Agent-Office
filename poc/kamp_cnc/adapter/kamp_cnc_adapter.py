"""Fail-closed row adapter for the isolated KAMP CNC PoC."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from poc.kamp_cnc.contracts.cnc_observation import (
    ADAPTER_VERSION,
    CONTRACT_VERSION,
    DATASET_NAME,
    FEATURE_COLUMNS,
    STATISTICS,
    AXES,
    CNCObservation,
)


REQUIRED_METADATA = ("SerialNo", "ReceivedDateTime", "passorfail")


class AdapterValidationError(ValueError):
    """Raised when a source row violates the adapter contract."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class PairMetadata:
    paired_serial: bool
    same_timestamp_pair: bool
    paired_label_status: str
    feature_vector_distinct: bool | None

    @classmethod
    def unpaired(cls) -> "PairMetadata":
        return cls(False, False, "NOT_PAIRED", None)


class KAMPCNCAdapter:
    source = "KAMP"
    equipment_type = "CNC_PRECISION_MACHINING"

    @staticmethod
    def read_csv(path: str | Path) -> list[dict[str, str]]:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise AdapterValidationError("MISSING_HEADER", "CSV header is missing")
            missing = [c for c in (*REQUIRED_METADATA, *FEATURE_COLUMNS) if c not in reader.fieldnames]
            if missing:
                raise AdapterValidationError("MISSING_COLUMNS", f"required columns missing: {missing}")
            return [dict(row) for row in reader]

    @classmethod
    def build_pair_index(cls, rows: Iterable[Mapping[str, Any]]) -> dict[int, PairMetadata]:
        materialized = list(rows)
        grouped: dict[str, list[int]] = defaultdict(list)
        for row_index, row in enumerate(materialized):
            serial = str(row.get("SerialNo", "")).strip()
            grouped[serial].append(row_index)

        result: dict[int, PairMetadata] = {}
        for indices in grouped.values():
            if len(indices) == 1:
                result[indices[0]] = PairMetadata.unpaired()
                continue

            group = [materialized[i] for i in indices]
            timestamps = {str(row.get("ReceivedDateTime", "")).strip() for row in group}
            raw_labels = [str(row.get("passorfail", "")).strip() for row in group]
            pass_fail_pair = len(group) == 2 and sorted(raw_labels) == ["0", "1"]
            status = "PASS_FAIL_PAIR" if pass_fail_pair else "UNEXPECTED_PAIRED_LABELS"
            distinct = len({tuple(str(row.get(c, "")) for c in FEATURE_COLUMNS) for row in group}) > 1
            metadata = PairMetadata(True, len(timestamps) == 1, status, distinct)
            for row_index in indices:
                result[row_index] = metadata
        return result

    def adapt_row(
        self,
        row: Mapping[str, Any],
        row_index: int,
        pair_metadata: PairMetadata | None = None,
    ) -> CNCObservation:
        if not isinstance(row_index, int) or row_index < 0:
            raise AdapterValidationError("INVALID_ROW_INDEX", "row_index must be a non-negative integer")

        for field in REQUIRED_METADATA:
            if field not in row or row[field] is None or str(row[field]).strip() == "":
                raise AdapterValidationError("MISSING_METADATA", f"required metadata missing: {field}")

        serial_no = str(row["SerialNo"]).strip()
        received_at = self._parse_timestamp(row["ReceivedDateTime"])
        raw_label = self._parse_label(row["passorfail"])

        missing_features = [c for c in FEATURE_COLUMNS if c not in row]
        if missing_features:
            raise AdapterValidationError("MISSING_FEATURE", f"required feature columns missing: {missing_features}")

        values = {column: self._parse_number(column, row[column]) for column in FEATURE_COLUMNS}
        process_features = self._map_features(values)
        status = "PASS" if raw_label == 0 else "FAIL"
        pair = pair_metadata or PairMetadata.unpaired()
        sample_id = self._sample_id(row_index, serial_no, received_at)

        return CNCObservation(
            source=self.source,
            dataset=DATASET_NAME,
            equipment_type=self.equipment_type,
            observation={
                "sample_id": sample_id,
                "row_index": row_index,
                "serial_no": serial_no,
                "received_at": received_at,
            },
            process_features=process_features,
            ground_truth={
                "raw_label": raw_label,
                "status": status,
                "source_type": "dataset_ground_truth",
                "prediction": False,
            },
            data_quality={
                "paired_serial": pair.paired_serial,
                "same_timestamp_pair": pair.same_timestamp_pair,
                "paired_label_status": pair.paired_label_status,
                "feature_vector_distinct": pair.feature_vector_distinct,
            },
            provenance={
                "dataset_name": DATASET_NAME,
                "source": "KAMP",
                "adapter_version": ADAPTER_VERSION,
                "contract_version": CONTRACT_VERSION,
            },
        )

    def adapt_all(self, rows: list[Mapping[str, Any]]) -> list[CNCObservation]:
        pair_index = self.build_pair_index(rows)
        return [self.adapt_row(row, i, pair_index[i]) for i, row in enumerate(rows)]

    @staticmethod
    def _parse_label(value: Any) -> int:
        if isinstance(value, bool):
            raise AdapterValidationError("INVALID_LABEL", "boolean is not a valid passorfail label")
        text = str(value).strip()
        if text not in {"0", "1"}:
            raise AdapterValidationError("INVALID_LABEL", f"passorfail must be 0 or 1, got {value!r}")
        return int(text)

    @staticmethod
    def _parse_timestamp(value: Any) -> str:
        text = str(value).strip()
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise AdapterValidationError("INVALID_TIMESTAMP", f"cannot parse ReceivedDateTime: {text!r}") from exc
        return parsed.isoformat(timespec="milliseconds")

    @staticmethod
    def _parse_number(column: str, value: Any) -> float:
        if value is None or str(value).strip() == "":
            raise AdapterValidationError("INVALID_NUMERIC", f"{column} is empty")
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise AdapterValidationError("INVALID_NUMERIC", f"{column} is not numeric: {value!r}") from exc
        if not math.isfinite(number):
            raise AdapterValidationError("INVALID_NUMERIC", f"{column} must be finite: {value!r}")
        return number

    @staticmethod
    def _map_features(values: Mapping[str, float]) -> dict[str, Any]:
        return {
            "spindle_speed": {stat: values[f"SpindleSpeed_{stat}"] for stat in STATISTICS},
            "servo_current": {
                axis: {stat: values[f"ServoCurrent_{axis}_{stat}"] for stat in STATISTICS}
                for axis in AXES
            },
            "servo_load": {
                axis: {stat: values[f"ServoLoad_{axis}_{stat}"] for stat in STATISTICS}
                for axis in AXES
            },
            "spindle_load": {stat: values[f"SpindleLoad_{stat}"] for stat in STATISTICS},
        }

    @staticmethod
    def _sample_id(row_index: int, serial_no: str, received_at: str) -> str:
        identity = json.dumps(
            [DATASET_NAME, row_index, serial_no, received_at],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        return f"kamp-cnc-{digest}"

