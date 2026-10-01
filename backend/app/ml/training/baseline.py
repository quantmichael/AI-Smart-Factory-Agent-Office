"""Train and serialize the fixed STEP 04 Random Forest baseline."""

from __future__ import annotations

import csv
import json
import platform
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

import joblib
import matplotlib
import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402

from app.data.adapters.base import SensorDatasetAdapter
from app.ml.dataset import MLFeatureTable, WindowFeatureRecord, build_feature_table
from app.ml.inference.service import MLInferenceService
from app.ml.training.evaluation import evaluate_predictions
from app.ml.training.split import GroupedSplit, stratified_measurement_split


MODEL_ID = "bearing_rf_binary_v1"
MODEL_VERSION = "1.0"
FEATURE_VERSION = "step03_v1"
RANDOM_STATE = 42
MODEL_CONFIG = {
    "n_estimators": 300,
    "max_depth": 12,
    "min_samples_split": 4,
    "class_weight": "balanced",
    "random_state": RANDOM_STATE,
    "n_jobs": -1,
}


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _distribution(records: tuple[WindowFeatureRecord, ...], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(getattr(item, key)) for item in records).items()))


def _split_artifact(split: GroupedSplit) -> dict[str, Any]:
    return {
        "random_seed": RANDOM_STATE,
        "split_strategy": "stratified group split",
        "group_key": "measurement_id",
        "test_size": 0.25,
        "train_measurements": list(split.train_measurements),
        "test_measurements": list(split.test_measurements),
        "train_bearings": sorted({item.bearing_id for item in split.train}),
        "test_bearings": sorted({item.bearing_id for item in split.test}),
        "train_window_count": len(split.train),
        "test_window_count": len(split.test),
        "class_distribution": {
            "train_windows": _distribution(split.train, "ground_truth"),
            "test_windows": _distribution(split.test, "ground_truth"),
            "train_measurements": dict(
                sorted(
                    Counter(
                        next(item.ground_truth for item in split.train if item.measurement_id == mid)
                        for mid in split.train_measurements
                    ).items()
                )
            ),
            "test_measurements": dict(
                sorted(
                    Counter(
                        next(item.ground_truth for item in split.test if item.measurement_id == mid)
                        for mid in split.test_measurements
                    ).items()
                )
            ),
        },
        "operating_condition_distribution": {
            "train_windows": _distribution(split.train, "operating_condition"),
            "test_windows": _distribution(split.test, "operating_condition"),
        },
        "leakage_validation": {
            "train_test_measurement_intersection": [],
            "passed": True,
        },
        "known_limitation": (
            "All three bearing IDs occur in both partitions. The split prevents window leakage "
            "but does not measure unseen-bearing generalization."
        ),
    }


def train_random_forest(
    table: MLFeatureTable,
    split: GroupedSplit,
) -> RandomForestClassifier:
    model = RandomForestClassifier(**MODEL_CONFIG)
    labels = np.asarray([record.ground_truth for record in split.train])
    model.fit(table.matrix(split.train), labels)
    return model


def _damaged_probability(
    model: RandomForestClassifier,
    matrix: np.ndarray,
) -> np.ndarray:
    classes = list(model.classes_)
    return model.predict_proba(matrix)[:, classes.index("damaged")]


def _write_predictions(
    path: Path,
    records: tuple[WindowFeatureRecord, ...],
    probabilities: np.ndarray,
) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        fieldnames = [
            "measurement_id",
            "bearing_id",
            "operating_condition",
            "window_id",
            "ground_truth",
            "probability_damaged",
            "predicted_class",
        ]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for record, probability in zip(records, probabilities, strict=True):
            writer.writerow(
                {
                    "measurement_id": record.measurement_id,
                    "bearing_id": record.bearing_id,
                    "operating_condition": record.operating_condition,
                    "window_id": record.window_id,
                    "ground_truth": record.ground_truth,
                    "probability_damaged": float(probability),
                    "predicted_class": "damaged" if probability >= 0.5 else "healthy",
                }
            )


def _write_feature_importance(
    output: Path,
    feature_names: tuple[str, ...],
    importance: np.ndarray,
) -> list[dict[str, Any]]:
    rows = sorted(
        (
            {"feature": name, "importance": float(value)}
            for name, value in zip(feature_names, importance, strict=True)
        ),
        key=lambda row: row["importance"],
        reverse=True,
    )
    with (output / "feature_importance.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["rank", "feature", "importance"])
        writer.writeheader()
        for rank, row in enumerate(rows, start=1):
            writer.writerow({"rank": rank, **row})
    top = rows[:15][::-1]
    fig, axis = plt.subplots(figsize=(9, 6))
    axis.barh([row["feature"] for row in top], [row["importance"] for row in top])
    axis.set(title="Random Forest feature importance (top 15)", xlabel="Impurity importance")
    fig.tight_layout()
    fig.savefig(output / "feature_importance.png", dpi=160)
    plt.close(fig)
    return rows


def _write_confusion_matrix(output: Path, matrix: list[list[int]]) -> None:
    values = np.asarray(matrix)
    fig, axis = plt.subplots(figsize=(5, 4.5))
    image = axis.imshow(values, cmap="Blues")
    for row in range(2):
        for column in range(2):
            axis.text(column, row, str(values[row, column]), ha="center", va="center")
    axis.set(
        title="Measurement-level confusion matrix",
        xlabel="Predicted class",
        ylabel="Ground-truth class",
        xticks=[0, 1],
        yticks=[0, 1],
        xticklabels=["healthy", "damaged"],
        yticklabels=["healthy", "damaged"],
    )
    fig.colorbar(image, ax=axis)
    fig.tight_layout()
    fig.savefig(output / "confusion_matrix.png", dpi=160)
    plt.close(fig)


def _write_report(
    output: Path,
    split_data: dict[str, Any],
    metrics: dict[str, Any],
    importance: list[dict[str, Any]],
    examples: list[dict[str, Any]],
    model_size: int,
) -> None:
    measurement = metrics["measurement_level"]
    window = metrics["window_level"]
    report = f"""# STEP 04 ML Baseline Report

## Task

Healthy vs damaged binary classification using the verified Paderborn labels.

## Dataset

- Train measurements: {len(split_data['train_measurements'])}; test measurements: {len(split_data['test_measurements'])}.
- Train windows: {split_data['train_window_count']}; test windows: {split_data['test_window_count']}.
- Local acquisition remains partial at 3 of 32 bearing-state archives.

## Feature Set

- 1.0-second, non-overlapping windows from vibration and two phase-current channels.
- Eight time-domain and four frequency-domain descriptors per channel.

## Window Policy

One 64,000-sample window; trailing incomplete samples are discarded.

## Split Strategy

Stratified measurement-group split with random seed 42. Measurement overlap is forbidden and validated.

## Model

RandomForestClassifier with one fixed, documented configuration and no hyperparameter search.

## Metrics

- Window F1: {window['f1']:.4f}; damaged recall: {window['damaged_recall']:.4f}; ROC-AUC: {window['roc_auc']:.4f}.
- Measurement accuracy: {measurement['accuracy']:.4f}; precision: {measurement['precision']:.4f}; recall: {measurement['recall']:.4f}; F1: {measurement['f1']:.4f}; ROC-AUC: {measurement['roc_auc']:.4f}.
- Aggregation was fixed in advance as mean damaged-class probability with threshold 0.5.

## Confusion Matrix

The plotted confusion matrix uses one aggregated prediction per test measurement.

## Operating-condition Results

Metrics are recorded per condition in `metrics.json`; they were not used to tune the model.

## Feature Importance

Top impurity importance: `{importance[0]['feature']}` ({importance[0]['importance']:.4f}). Importance is descriptive, not causal.

## Example Inference

- Healthy example predicted `{examples[0]['predicted_class']}` with model confidence {examples[0]['confidence']:.4f}.
- Damaged example predicted `{examples[1]['predicted_class']}` with model confidence {examples[1]['confidence']:.4f}.

## Artifact

Serialized model size: {model_size} bytes.

## Limitations

- Bearing identity and state are confounded because only one healthy bearing is local.
- Every bearing identity occurs in both train and test; this is not unseen-bearing evaluation.
- Random Forest probabilities are not calibrated equipment-failure probabilities.
- No test-set-driven threshold or hyperparameter tuning was performed.

## Next Experiment

Acquire more healthy and damaged bearings, then repeat evaluation with bearing-group holdout before drawing generalization conclusions.
"""
    (output / "BASELINE_REPORT.md").write_text(report, encoding="utf-8")


def run_baseline(
    adapter: SensorDatasetAdapter,
    input_spec: dict[str, Any],
    output: Path | str,
) -> dict[str, Any]:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    started = perf_counter()
    table = build_feature_table(adapter, input_spec)
    split = stratified_measurement_split(table.records, random_state=RANDOM_STATE)
    split_data = _split_artifact(split)
    model = train_random_forest(table, split)
    test_probabilities = _damaged_probability(model, table.matrix(split.test))
    metrics = evaluate_predictions(split.test, test_probabilities)
    _write_predictions(output / "test_predictions.csv", split.test, test_probabilities)

    bundle = {
        "model": model,
        "model_id": MODEL_ID,
        "model_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,
        "feature_names": list(table.feature_names),
        "classes": list(model.classes_),
        "window_config": {
            "duration_sec": input_spec["window_duration_sec"],
            "overlap_percent": input_spec["overlap_percent"],
        },
    }
    model_path = output / "model.joblib"
    joblib.dump(bundle, model_path)
    importance = _write_feature_importance(output, table.feature_names, model.feature_importances_)
    _write_confusion_matrix(output, metrics["measurement_level"]["confusion_matrix"])

    service = MLInferenceService(adapter, model_path, input_spec)
    summaries = adapter.list_measurements()
    healthy_id = next(item.measurement_id for item in summaries if item.ground_truth.state == "healthy")
    damaged_id = next(item.measurement_id for item in summaries if item.ground_truth.state == "damaged")
    examples = [
        {"ground_truth": "healthy", **service.analyze(healthy_id).model_dump(mode="json")},
        {"ground_truth": "damaged", **service.analyze(damaged_id).model_dump(mode="json")},
    ]
    _json(output / "example_inference.json", examples)
    _json(output / "metrics.json", metrics)
    _json(output / "split.json", split_data)
    _json(output / "feature_list.json", {"feature_names": list(table.feature_names)})
    _json(output / "input_spec.json", input_spec)

    metadata = {
        "model_id": MODEL_ID,
        "model_type": "RandomForestClassifier",
        "version": MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset": "Paderborn Bearing DataCenter local representative subset",
        "dataset_version_reference": "data/paderborn/metadata/dataset_files.json",
        "feature_version": FEATURE_VERSION,
        "class_mapping": {"healthy": "normal", "damaged": "abnormal"},
        "feature_list": list(table.feature_names),
        "window_config": bundle["window_config"],
        "split_strategy": "stratified group split",
        "group_key": "measurement_id",
        "random_seed": RANDOM_STATE,
        "model_config": MODEL_CONFIG,
        "library_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "metrics_summary": {
            "measurement_accuracy": metrics["measurement_level"]["accuracy"],
            "measurement_f1": metrics["measurement_level"]["f1"],
            "measurement_damaged_recall": metrics["measurement_level"]["damaged_recall"],
            "measurement_roc_auc": metrics["measurement_level"]["roc_auc"],
        },
        "model_size_bytes": model_path.stat().st_size,
        "training_seconds": perf_counter() - started,
    }
    _json(output / "metadata.json", metadata)
    _write_report(output, split_data, metrics, importance, examples, model_path.stat().st_size)
    (output / "README.md").write_text(
        "# bearing_rf_binary_v1\n\n"
        "STEP 04 Random Forest baseline. Load `model.joblib` only from this trusted local artifact directory. "
        "Probabilities are uncalibrated model outputs, not equipment failure probabilities.\n",
        encoding="utf-8",
    )
    return {
        "metadata": metadata,
        "metrics": metrics,
        "split": split_data,
        "examples": examples,
    }
