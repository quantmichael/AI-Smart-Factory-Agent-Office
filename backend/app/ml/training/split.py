"""Deterministic measurement-group split for the STEP 04 baseline."""

from __future__ import annotations

from dataclasses import dataclass

from sklearn.model_selection import train_test_split

from app.ml.dataset import WindowFeatureRecord
from app.ml.splitting import assert_no_group_leakage


@dataclass(frozen=True, slots=True)
class GroupedSplit:
    train: tuple[WindowFeatureRecord, ...]
    test: tuple[WindowFeatureRecord, ...]
    train_measurements: tuple[str, ...]
    test_measurements: tuple[str, ...]


def stratified_measurement_split(
    records: tuple[WindowFeatureRecord, ...],
    *,
    test_size: float = 0.25,
    random_state: int = 42,
) -> GroupedSplit:
    labels_by_measurement: dict[str, str] = {}
    for record in records:
        previous = labels_by_measurement.setdefault(record.measurement_id, record.ground_truth)
        if previous != record.ground_truth:
            raise ValueError(f"inconsistent label for {record.measurement_id}")
    measurement_ids = sorted(labels_by_measurement)
    labels = [labels_by_measurement[item] for item in measurement_ids]
    train_ids, test_ids = train_test_split(
        measurement_ids,
        test_size=test_size,
        random_state=random_state,
        stratify=labels,
    )
    train_set = frozenset(train_ids)
    test_set = frozenset(test_ids)
    assert_no_group_leakage(train_set, test_set)
    train = tuple(record for record in records if record.measurement_id in train_set)
    test = tuple(record for record in records if record.measurement_id in test_set)
    if not train or not test:
        raise ValueError("split produced an empty partition")
    return GroupedSplit(
        train=train,
        test=test,
        train_measurements=tuple(sorted(train_set)),
        test_measurements=tuple(sorted(test_set)),
    )
