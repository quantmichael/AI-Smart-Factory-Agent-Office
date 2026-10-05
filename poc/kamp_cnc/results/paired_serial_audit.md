# KAMP CNC Paired Serial Audit — K1-A.1

## Scope

- Input: `poc/kamp_cnc/data/raw/정밀가공_품질보증_데이터셋.csv`
- Pair: the same `SerialNo` occurring exactly twice.
- Difference sign: `FAIL - PASS`.
- Identifier and label columns are excluded from Feature comparison.
- No source row was modified or removed. No ML training, Adapter implementation, RAG work, Production test, or DB write was performed.

## 1. Paired sample

- Two-row `SerialNo` groups: **99**.
- Same `SerialNo`: **99/99**.
- Same `ReceivedDateTime` within the pair: **99/99**.
- Exactly one PASS and one FAIL: **99/99**.
- Pairs with all 40 Feature values identical and only the label different: **0**.
- Pairs with at least one different Feature: **99**.

All 99 pairs are distinct Feature vectors. This establishes value-level difference only. The CSV does not establish whether the rows are independent physical measurements or explain why the identifier and timestamp are shared.

## 2. Difference method

- Mean and median difference use `FAIL - PASS`.
- Absolute difference is summarized by the mean and median of `abs(FAIL - PASS)` across 99 pairs.
- Symmetric relative difference is `(FAIL-PASS) / ((abs(FAIL)+abs(PASS))/2)`. A both-zero denominator is recorded as zero.
- Cross-Feature standardized difference divides the absolute pair difference by that Feature's population standard deviation over the 198 paired rows.
- Overall pair magnitude is the RMS of the standardized differences across 27 nonconstant Features.
- Constants are excluded from standardized interpretation.
- No binary threshold defines “almost identical” or “clearly different.” Exact equality, observed ranks, and distribution quantiles are reported instead.

## 3. Feature differences

### Features that differ within pairs

| Feature | PASS mean | FAIL mean | Mean diff | Median diff | Mean abs diff | Mean abs relative diff | FAIL > PASS | FAIL < PASS | Equal |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SpindleSpeed_max | 2226.326 | 2220.815 | -5.510 | 0.000 | 5.510 | 0.2481% | 0 | 49 | 50 |
| ServoCurrent_X_max | 1131.547 | 1148.527 | 16.980 | -13.150 | 39.607 | 3.4347% | 49 | 50 | 0 |
| SpindleSpeed_mean | 1188.958 | 1206.075 | 17.117 | -14.015 | 41.306 | 3.4347% | 49 | 50 | 0 |
| ServoCurrent_X_mean | 150.142 | 140.463 | -9.680 | -5.025 | 9.680 | 6.7482% | 0 | 99 | 0 |
| SpindleSpeed_std | 868.046 | 868.108 | 0.062 | 7.730 | 8.680 | 1.0000% | 50 | 49 | 0 |
| ServoCurrent_X_std | 149.755 | 140.173 | -9.582 | -6.393 | 9.582 | 6.7482% | 0 | 99 | 0 |
| ServoLoad_X_std | 18.276 | 19.653 | 1.377 | 1.227 | 1.377 | 7.1775% | 99 | 0 | 0 |
| ServoLoad_Z3_std | 195.614 | 210.509 | 14.895 | 6.428 | 14.895 | 7.1775% | 99 | 0 | 0 |
| SpindleLoad_max | 31692.244 | 32649.202 | 956.957 | 1495.535 | 956.957 | 2.9561% | 99 | 0 | 0 |
| SpindleLoad_mean | 3323.665 | 3110.528 | -213.136 | -110.330 | 213.136 | 6.7482% | 0 | 99 | 0 |
| SpindleLoad_std | 4880.808 | 5245.014 | 364.206 | 257.349 | 364.206 | 7.1775% | 99 | 0 | 0 |

### Nonconstant Features that remain equal in every pair

The following 16 Features vary across the dataset but are exactly equal between PASS and FAIL within all 99 pairs:

- `ServoCurrent_Z1_max`, `ServoCurrent_Z3_max`
- `ServoLoad_X_max`, `ServoLoad_Z1_max`, `ServoLoad_Z3_max`
- `ServoCurrent_Z1_mean`, `ServoCurrent_Z3_mean`
- `ServoLoad_X_mean`, `ServoLoad_Z1_mean`, `ServoLoad_Z3_mean`
- `ServoCurrent_X_min`, `ServoCurrent_Z1_min`, `ServoLoad_Z1_min`
- `ServoCurrent_Z1_std`, `ServoCurrent_Z3_std`, `ServoLoad_Z1_std`

### Constant Features excluded from interpretation

- `ServoCurrent_Z2_max`, `ServoLoad_Z2_max`
- `ServoCurrent_Z2_mean`, `ServoLoad_Z2_mean`
- `SpindleSpeed_min`, `ServoCurrent_Z2_min`, `ServoCurrent_Z3_min`
- `ServoLoad_X_min`, `ServoLoad_Z2_min`, `ServoLoad_Z3_min`
- `ServoCurrent_Z2_std`, `ServoLoad_Z2_std`, `SpindleLoad_min`

### Largest scale-adjusted differences

Ranking by mean absolute paired difference divided by the Feature standard deviation across paired rows:

1. `SpindleLoad_max`: 1.2966
2. `SpindleSpeed_max`: 1.0416
3. `ServoCurrent_X_mean`: 1.0052
4. `SpindleLoad_std`: 0.7079
5. `SpindleLoad_mean`: 0.3982

## 4. Pair-level differences

- Different Feature count: minimum 10, median 10, maximum 11.
- Exactly 10 Features differ: **50 pairs**.
- Exactly 11 Features differ: **49 pairs**.
- Same Feature count: 30 for 50 pairs and 29 for 49 pairs.
- The additional eleventh difference is `SpindleSpeed_max`, which is equal in 50 pairs and lower in FAIL for 49 pairs.

Overall standardized RMS magnitude distribution:

| Quantile | Magnitude |
|---:|---:|
| minimum | 0.4211 |
| 10% | 0.4402 |
| 25% | 0.4462 |
| median | 0.4512 |
| 75% | 0.5890 |
| 90% | 0.5949 |
| maximum | 0.6154 |

The closest observed pair is `20220824-0000062` at 0.4211. The most different observed pair is `20220823-0000210` at 0.6154. These are observed ranks, not threshold-based “same/different” categories. Even the closest pair differs in 10 Features.

### Exact paired patterns

The differences form two exact ratio patterns:

- **50 pairs:** FAIL/PASS ratios are 0.97 for `ServoCurrent_X_mean`, `ServoCurrent_X_std`, and `SpindleLoad_mean`; 1.05 for `ServoLoad_X_std`, `ServoLoad_Z3_std`, `SpindleLoad_std`, and `SpindleLoad_max`; 1.00 for `SpindleSpeed_max`; 0.98 for `ServoCurrent_X_max` and `SpindleSpeed_mean`; and 1.01 for `SpindleSpeed_std`.
- **49 pairs:** ratios are 0.90 for `ServoCurrent_X_mean`, `ServoCurrent_X_std`, and `SpindleLoad_mean`; 1.10 for `ServoLoad_X_std`, `ServoLoad_Z3_std`, and `SpindleLoad_std`; 1.01 for `SpindleLoad_max`; 0.995 for `SpindleSpeed_max`; 1.05 for `ServoCurrent_X_max` and `SpindleSpeed_mean`; and 0.99 for `SpindleSpeed_std`.

This is strong evidence that the PASS and FAIL rows are systematically different Feature vectors. It also means they should not be assumed statistically independent until their generation or collection provenance is confirmed. No origin for these exact patterns is inferred.

## 5. Guidebook direction cross-check

The Guidebook describes positive association for `SpindleLoad_max` and `SpindleLoad_std`, and negative association for `SpindleSpeed_max` and `ServoCurrent_X_mean`.

| Feature | Expected direction | Agreement | Disagreement | Equal | Paired mean diff | Paired median diff |
|---|---|---:|---:|---:|---:|---:|
| SpindleLoad_max | FAIL > PASS | 99/99 | 0 | 0 | 956.957 | 1495.535 |
| SpindleLoad_std | FAIL > PASS | 99/99 | 0 | 0 | 364.206 | 257.349 |
| SpindleSpeed_max | FAIL < PASS | 49/99 | 0 | 50 | -5.510 | 0.000 |
| ServoCurrent_X_mean | FAIL < PASS | 99/99 | 0 | 0 | -9.680 | -5.025 |

All non-equal paired changes agree with the Guidebook directions. Three variables agree in every pair; `SpindleSpeed_max` agrees in 49 pairs and is unchanged in 50. This is directional consistency only and does not establish causality or physical independence.

## 6. Interpretation

**Verdict: DISTINCT_OBSERVATIONS**

Every pair has a different Feature vector, with 10 or 11 changed Features, and no pair differs only by its label. The differences are systematic and align with the four Guidebook directions. This supports treating them as distinct row-level observations rather than duplicate rows with a changed label.

The verdict is limited to stored Feature values. The same identifier, same timestamp, and exact two-pattern ratio structure remain unresolved provenance and data-quality concerns. The available files do not prove the rows are separate physical production measurements.

## 7. ML implication

- **Independent row usage: HOLD pending provenance.** The rows are distinct vectors, but statistical or physical independence is not established.
- **SerialNo Group Split: required.** Both rows of a pair must remain in the same fold.
- **Random row split: not allowed.** It can place the paired record in both train and evaluation sets and inflate performance.
- **Data-quality flag: required.** Record `paired_serial=true`, `same_timestamp=true`, and `conflicting_labels=true` without changing the source label.
- A baseline should start only after the paired-row generation/collection rule is confirmed or the experiment is explicitly scoped as a dataset-behavior PoC rather than a production-generalization evaluation.

## 8. Next-step decision

- **CNC Adapter PoC: GO.** Preserve each source row and expose pair/conflict metadata. Do not merge rows or infer a product-level label.
- **ML Baseline PoC: HOLD.** Wait for provenance clarification and a documented treatment of the paired structure.

