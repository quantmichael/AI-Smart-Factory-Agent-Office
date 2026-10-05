# KAMP CNC Dataset Audit — K1-A

## Scope and evidence rule

- Values and structure: the CSV is the source of truth.
- Meaning, label definition, and stated collection/processing method: the official Guidebook is the reference.
- This was a read-only audit. No adapter, ML training, RAG, production test, or DB write was performed.

## 1. Dataset integrity

- Shape: **1,085 rows × 43 columns**.
- Dtypes: `SerialNo` and `ReceivedDateTime` load as `object`; all 40 process features are `float64`; `passorfail` is `int64`. Every `ReceivedDateTime` value parses successfully as a datetime.
- Missing values: **0**.
- Full duplicate rows: **0**.
- Observed date range: **2022-08-23 03:14:36.906 — 2022-08-25 10:14:44.102**.
- Rows by observed date: 2022-08-23 = 337, 2022-08-24 = 338, 2022-08-25 = 410.
- Labels: only `0` and `1` occur.
- Mapping: `0 = PASS / 양품`, `1 = FAIL / 불량`; this matches the Guidebook.
- PASS: **986 (90.8756%)**.
- FAIL: **99 (9.1244%)**.
- Class ratio: **986:99 = 9.9596:1**.

## 2. SerialNo and ground truth

- Unique `SerialNo`: **986**.
- Duplicate rows beyond the first by `SerialNo`: **99**.
- Products appearing once: **887**; appearing twice: **99**; no product appears more than twice.
- All 99 repeated `SerialNo` groups have exactly the same `ReceivedDateTime` within the group.
- All 99 repeated groups have different process-feature vectors, so they are not full-row duplicates.
- All 99 repeated groups contain both `passorfail=0` and `passorfail=1`: **99 conflicting identifiers / 198 affected rows**.
- Representative cases: `20220823-0000210`, `20220823-0000219`, and `20220823-0000231`; each has the same timestamp on both rows and labels `[0, 1]`.
- The CSV and Guidebook do not explain why these pairs exist. No cause, deduplication rule, or replacement label is inferred.

The Guidebook defines `SerialNo` as a product number and says one row represents one product. The repeated, same-time, conflicting-label structure therefore prevents an unqualified product-level ground-truth contract. `SerialNo` is still the required ML grouping key to prevent a product number from crossing folds, but grouping alone does not resolve the contradictory labels.

## 3. Feature contract

### Metadata

- `SerialNo`
- `ReceivedDateTime`

### SpindleSpeed

- `SpindleSpeed_max`, `SpindleSpeed_mean`, `SpindleSpeed_min`, `SpindleSpeed_std`

### ServoCurrent

- X: `ServoCurrent_X_max`, `ServoCurrent_X_mean`, `ServoCurrent_X_min`, `ServoCurrent_X_std`
- Z1: `ServoCurrent_Z1_max`, `ServoCurrent_Z1_mean`, `ServoCurrent_Z1_min`, `ServoCurrent_Z1_std`
- Z2: `ServoCurrent_Z2_max`, `ServoCurrent_Z2_mean`, `ServoCurrent_Z2_min`, `ServoCurrent_Z2_std`
- Z3: `ServoCurrent_Z3_max`, `ServoCurrent_Z3_mean`, `ServoCurrent_Z3_min`, `ServoCurrent_Z3_std`

### ServoLoad

- X: `ServoLoad_X_max`, `ServoLoad_X_mean`, `ServoLoad_X_min`, `ServoLoad_X_std`
- Z1: `ServoLoad_Z1_max`, `ServoLoad_Z1_mean`, `ServoLoad_Z1_min`, `ServoLoad_Z1_std`
- Z2: `ServoLoad_Z2_max`, `ServoLoad_Z2_mean`, `ServoLoad_Z2_min`, `ServoLoad_Z2_std`
- Z3: `ServoLoad_Z3_max`, `ServoLoad_Z3_mean`, `ServoLoad_Z3_min`, `ServoLoad_Z3_std`

### SpindleLoad

- `SpindleLoad_max`, `SpindleLoad_mean`, `SpindleLoad_min`, `SpindleLoad_std`

### Ground truth

- `passorfail`

### Variance and identical-feature findings

There are **13 constant columns**:

- Constant 30.3: `ServoCurrent_Z2_max`, `ServoLoad_Z2_max`, `ServoCurrent_Z2_mean`, `ServoLoad_Z2_mean`, `ServoCurrent_Z2_min`, `ServoLoad_Z2_min`.
- Constant 0.0: `SpindleSpeed_min`, `ServoLoad_X_min`, `ServoCurrent_Z2_std`, `ServoLoad_Z2_std`, `SpindleLoad_min`.
- Constant 40.4: `ServoCurrent_Z3_min`, `ServoLoad_Z3_min`.

No additional non-constant near-zero-variance feature was found using the explicit rule: unique percentage ≤10% and most-common/second-most-common frequency ratio >19. No non-constant feature pair is exactly identical. The identical column pairs are entirely explained by the constant-value groups above.

## 4. Guidebook cross-check

### Matched

- 1,085 rows and 43 columns.
- PASS 986 and FAIL 99.
- `passorfail`: 0 = 양품, 1 = 불량.
- `SerialNo`: object and product number.
- Feature families based on max / mean / min / std.
- Thirteen numeric constants; removing them and two object columns leaves 28 columns, as shown by the Guidebook workflow.
- All CSV timestamps fall within the Guidebook's validity interval of 2022-08-23 through 2022-08-27.
- PLC/sensor collection, raw sampling at 10–100 ms, and product-level feature engineering are official Guidebook descriptions; they cannot be independently proven from the final aggregate CSV alone.

### Guidebook final nine variables

1. `SpindleSpeed_max`
2. `ServoLoad_Z1_max`
3. `ServoCurrent_X_mean`
4. `ServoCurrent_X_std`
5. `ServoLoad_X_std`
6. `SpindleLoad_max`
7. `upper_mold_temp1`
8. `SpindleLoad_mean`
9. `SpindleLoad_std`

### Inconsistencies

1. `upper_mold_temp1` is **not present** in the actual 43-column CSV. It was not replaced by another variable.
2. The stated collection period ends on 2022-08-27, but the latest timestamp actually present is 2022-08-25 10:14:44.102. The rows are within the stated period but do not cover its final two dates.
3. The Guidebook says one row represents one product and `SerialNo` is the product number. The CSV has 99 product numbers with two same-time rows and conflicting labels.
4. The Guidebook's reported SerialNo uniqueness of 90.9% matches `986 / 1,085`, but the reason and ground-truth handling for the 99 conflicting groups are not documented.

## 5. Leakage risks and safe evaluation design

1. **Random row split — high:** the same `SerialNo` and timestamp can enter both train and test.
2. **Ground-truth conflict — critical:** every repeated `SerialNo` contains both labels; this must not be silently deduplicated or relabeled.
3. **Temporal dependence — high:** only three observed dates are present, so random mixing can hide day or batch drift.
4. **Feature-selection leakage — high:** the Guidebook's T-test selection occurs before its train/test split. Reusing this order would expose evaluation labels to selection.
5. **SMOTE leakage — critical if done before splitting:** SMOTE must be applied only to training partitions. The Guidebook applies it after the row split, but that row split is not group-safe.
6. **Preprocessing leakage — high:** imputation, outlier thresholds, constant filtering, scaling/normalization, and feature selection must be fit only on each training partition.

Safe design: first obtain an authoritative rule for the 99 conflicting labels; keep all rows with the same `SerialNo` in one group; use a forward temporal holdout where sample size allows; perform every preprocessing and selection step inside training folds; apply SMOTE only after splitting and only to training data; report class-aware metrics and uncertainty.

## 6. PoC suitability

| Purpose | Rating | Reason |
|---|---|---|
| CNC Adapter PoC | **GOOD** | The raw schema and row-level values are usable if the adapter preserves all rows and exposes conflicts without deciding labels. |
| Ground Truth Context PoC | **LIMITED** | The 0/1 meaning is official, but 99 product identifiers have contradictory ground truth. |
| CNC RAG PoC | **LIMITED** | The Guidebook is useful, but answers must disclose the `upper_mold_temp1` and label inconsistencies. |
| Simple ML Baseline PoC | **LIMITED** | Possible only after authoritative label handling and group/temporal leakage controls. |
| DNN performance evaluation | **NOT RECOMMENDED** | The data is small, imbalanced, covers three observed days, and contains unresolved product-level label conflicts. |
| Production/generalization claim | **NOT RECOMMENDED** | There is no independent site/machine/time holdout, and ground truth is unresolved. |

## 7. Verdict

- **K1-A: PASS** — the read-only audit completed and all identified inconsistencies are recorded. This does not mean the dataset is production-ready.
- **K1-B Adapter Implementation: GO**, with mandatory safeguards: preserve all rows, never collapse a `SerialNo` or infer a label, surface the conflict state in the contract, and do not begin ML performance evaluation until the ground-truth conflict is resolved authoritatively.

