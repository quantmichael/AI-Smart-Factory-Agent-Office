"""Evaluation at window, measurement, bearing, and condition levels."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from app.ml.dataset import WindowFeatureRecord


def binary_metrics(y_true: Iterable[int], probability: Iterable[float]) -> dict[str, Any]:
    truth = np.asarray(tuple(y_true), dtype=np.int64)
    scores = np.asarray(tuple(probability), dtype=np.float64)
    predicted = (scores >= 0.5).astype(np.int64)
    roc_auc = float(roc_auc_score(truth, scores)) if np.unique(truth).size == 2 else None
    return {
        "sample_count": int(truth.size),
        "accuracy": float(accuracy_score(truth, predicted)),
        "precision": float(precision_score(truth, predicted, zero_division=0)),
        "recall": float(recall_score(truth, predicted, zero_division=0)),
        "f1": float(f1_score(truth, predicted, zero_division=0)),
        "roc_auc": roc_auc,
        "damaged_recall": float(recall_score(truth, predicted, zero_division=0)),
        "confusion_matrix": confusion_matrix(truth, predicted, labels=[0, 1]).tolist(),
    }


def aggregate_probabilities(
    records: tuple[WindowFeatureRecord, ...],
    probabilities: np.ndarray,
    key: str,
) -> list[dict[str, Any]]:
    grouped: defaultdict[str, list[tuple[WindowFeatureRecord, float]]] = defaultdict(list)
    for record, probability in zip(records, probabilities, strict=True):
        grouped[str(getattr(record, key))].append((record, float(probability)))
    return [
        {
            "group": group,
            "ground_truth": values[0][0].ground_truth,
            "probability_damaged": float(np.mean([item[1] for item in values])),
            "window_count": len(values),
        }
        for group, values in sorted(grouped.items())
    ]


def evaluate_predictions(
    records: tuple[WindowFeatureRecord, ...],
    probabilities: np.ndarray,
) -> dict[str, Any]:
    labels = np.asarray([record.ground_truth == "damaged" for record in records], dtype=int)
    measurement_rows = aggregate_probabilities(records, probabilities, "measurement_id")
    bearing_rows = aggregate_probabilities(records, probabilities, "bearing_id")
    condition_results: dict[str, Any] = {}
    for condition in sorted({record.operating_condition for record in records}):
        indices = [i for i, record in enumerate(records) if record.operating_condition == condition]
        condition_results[condition] = binary_metrics(labels[indices], probabilities[indices])

    def grouped_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
        return binary_metrics(
            [row["ground_truth"] == "damaged" for row in rows],
            [row["probability_damaged"] for row in rows],
        )

    return {
        "aggregation_rule": "mean damaged-class probability; threshold=0.5",
        "window_level": binary_metrics(labels, probabilities),
        "measurement_level": grouped_metrics(measurement_rows),
        "bearing_level": grouped_metrics(bearing_rows),
        "operating_condition": condition_results,
        "measurement_predictions": measurement_rows,
        "bearing_predictions": bearing_rows,
    }
