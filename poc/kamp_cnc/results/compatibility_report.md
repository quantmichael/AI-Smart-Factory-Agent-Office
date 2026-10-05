# KAMP CNC Adapter Compatibility Report — K1-B

## Contract and adapter

- Contract: `CNCObservation` version `1.0.0`
- Adapter: `KAMPCNCAdapter` version `1.0.0`
- Source: `KAMP`
- Dataset: `정밀가공_품질보증_데이터셋`
- Equipment type: `CNC_PRECISION_MACHINING`
- Stable ID: SHA-256 of dataset name, zero-based CSV data-row index, SerialNo, and normalized timestamp

The Adapter maps one CSV row to one observation. It does not merge paired rows, select Features, remove constants, alter labels, or infer why paired observations exist.

## Feature mapping

All 40 Process Features are preserved as finite numbers:

- `spindle_speed`: max, mean, min, std
- `servo_current`: X, Z1, Z2, Z3 × max, mean, min, std
- `servo_load`: X, Z1, Z2, Z3 × max, mean, min, std
- `spindle_load`: max, mean, min, std

The 13 constant Features identified during K1-A remain in every converted observation.

## Ground truth

- `passorfail=0` → `PASS`
- `passorfail=1` → `FAIL`
- `source_type=dataset_ground_truth`
- `prediction=false`

Ground truth is not an ML prediction.

## Paired observations

The Adapter preserves the 99 paired SerialNo groups as 198 separate observations. Each paired row records:

- `paired_serial=true`
- `same_timestamp_pair=true`
- `paired_label_status=PASS_FAIL_PAIR`
- `feature_vector_distinct=true`

No product-level label is selected or inferred.

## Full dataset compatibility

| Metric | Result |
|---|---:|
| Input rows | 1,085 |
| Converted observations | 1,085 |
| PASS | 986 |
| FAIL | 99 |
| Paired observation rows | 198 |
| Paired SerialNo groups | 99 |
| Validation failures | 0 |
| Unique sample IDs | 1,085 |
| Duplicate sample IDs | 0 |
| Feature values per observation | 40 |
| Feature value mismatches against source | 0 |

The full-dataset compatibility verdict is **PASS**.

The source contains no unpaired FAIL row. `adapter_examples.json` therefore records that limitation and uses an actual paired FAIL observation for the general FAIL mapping example. The unpaired FAIL code path is separately verified with a valid in-memory test fixture derived from a real row. The source CSV is not modified.

## Fail-closed validation

The Adapter raises `AdapterValidationError` for:

- labels other than 0 or 1
- missing required metadata
- missing required Feature columns
- empty, nonnumeric, NaN, or infinite Feature values
- unparseable timestamps
- invalid row indexes

It does not silently coerce or repair invalid source data.

## Tests

- Tests executed: 15
- Passed: 15
- Failed: 0
- Framework: Python standard-library `unittest`
- Production tests executed: no

The suite covers normal PASS, valid unpaired FAIL mapping, paired PASS, paired FAIL, ground-truth semantics, prediction separation, all 40 Features, paired metadata, deterministic sample ID, four fail-closed cases, missing metadata, and full-dataset conversion.

## Production isolation

- Production code changed by K1-B: none
- Production DB writes: 0
- Production imports from `poc/`: none
- Existing Production tests: not changed and not executed
- Existing DB, Checkpoint, Memory, Artifact, Chroma, ML model, and deployment configuration: not touched

Pre-existing unrelated modifications to two Frontend files and other untracked repository files remain outside this PoC and were not changed by K1-B.

## Next-step decisions

- **K1-B: PASS**
- **K2 CNC RAG PoC: GO**, provided retrieval preserves the official Guidebook/CSV distinction and surfaces known inconsistencies rather than resolving them silently.
- **ML Baseline PoC: HOLD** until the paired-observation provenance and statistical independence question has an authoritative treatment. Adapter compatibility does not resolve that ML validity risk.
