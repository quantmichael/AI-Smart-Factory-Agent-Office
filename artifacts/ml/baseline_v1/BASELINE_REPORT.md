# STEP 04 ML Baseline Report

## Task

Healthy vs damaged binary classification using the verified Paderborn labels.

## Dataset

- Train measurements: 180; test measurements: 60.
- Train windows: 718; test windows: 239.
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

- Window F1: 1.0000; damaged recall: 1.0000; ROC-AUC: 1.0000.
- Measurement accuracy: 1.0000; precision: 1.0000; recall: 1.0000; F1: 1.0000; ROC-AUC: 1.0000.
- Aggregation was fixed in advance as mean damaged-class probability with threshold 0.5.

## Confusion Matrix

The plotted confusion matrix uses one aggregated prediction per test measurement.

## Operating-condition Results

Metrics are recorded per condition in `metrics.json`; they were not used to tune the model.

## Feature Importance

Top impurity importance: `phase_current_1__mean` (0.1712). Importance is descriptive, not causal.

## Example Inference

- Healthy example predicted `healthy` with model confidence 1.0000.
- Damaged example predicted `damaged` with model confidence 1.0000.

## Artifact

Serialized model size: 267458 bytes.

## Limitations

- Bearing identity and state are confounded because only one healthy bearing is local.
- Every bearing identity occurs in both train and test; this is not unseen-bearing evaluation.
- Random Forest probabilities are not calibrated equipment-failure probabilities.
- No test-set-driven threshold or hyperparameter tuning was performed.

## Next Experiment

Acquire more healthy and damaged bearings, then repeat evaluation with bearing-group holdout before drawing generalization conclusions.
