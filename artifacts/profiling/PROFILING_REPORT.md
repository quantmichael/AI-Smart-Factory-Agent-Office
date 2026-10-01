# Paderborn Data Profiling Report

Generated: `2026-09-18T00:07:50+00:00`  
Profiling version: `1.0`  
Random state: `42`

## Dataset Summary

- 240 measurements from 3 local bearing states.
- Healthy: 80; damaged: 160; unknown: 0.
- Damaged-to-healthy measurement ratio: 2.0:1.
- Four operating conditions are equally represented with 60 measurements each.
- Source acquisition remains partial; conclusions apply only to K001, KA01, and KI01.

## Data Quality

- Adapter validation passed for every measurement; no empty, NaN, Inf, or duplicate measurement was found.
- Constant signals: 0.
- Sampling deviations above 5%: 6.
- Extreme-amplitude candidates: 0; these are flagged and retained, not treated as errors.
- Raw Unit metadata is unavailable, and HostService time axes are not uniformly spaced in all files.

## Signal Characteristics

- Diagnostic profiling uses `vibration_1`, `phase_current_1`, and `phase_current_2` at the verified nominal 64 kHz rate.
- Current/vibration sample counts vary across four-second files, so exact raw time axes remain authoritative.
- Full-measurement features retain measurement, bearing, condition, and state identifiers.

## Healthy vs Damaged

- Overall vibration RMS Cohen's d (damaged minus healthy): 1.150.
- Overall vibration kurtosis Cohen's d: 0.287.
- These are descriptive effects across only three bearings, not classification-performance estimates.

## Operating-condition Effects

- State comparisons are also calculated separately for every operating condition.
- Vibration RMS/kurtosis condition-mean relative spreads range from 0.099 to 0.543.
- Operating condition is retained as an input identifier and must not be ignored during evaluation.

## Frequency-domain Findings

- DC is removed and a Hann window is applied before the real FFT to reduce spectral leakage.
- Explored descriptors: dominant spectral peak, spectral centroid, spectral energy, and normalized spectral entropy.
- Features retained for the provisional STEP 04 baseline by mean within-condition |Cohen's d| >= 0.5: dominant_frequency_hz, spectral_centroid_hz, spectral_energy, spectral_entropy.
- No spectral peak is labeled as a bearing fault frequency because that interpretation is not validated here.

## Windowing Comparison

- Compared 0.25, 0.5, and 1.0 second windows at 0% and 50% overlap.
- Selected: 1.0 second, 0% overlap (64000 samples at 64 kHz).
- Observed total windows: 957; 3–4 per measurement.
- Reason: 1 Hz FFT-bin spacing, moderate compute cost, and less correlation/pseudo-replication than overlapping windows.
- Any trailing incomplete window is discarded and recorded through the per-measurement window counts.

## Leakage Risks

- Random window split is prohibited.
- Preferred bearing-group holdout is currently infeasible: Only one healthy bearing is local; a bearing holdout cannot preserve both classes in train and test.
- Provisional STEP 04 split groups by `measurement_id`; all windows from one measurement stay together.
- This prevents window leakage but does not estimate unseen-bearing generalization.

## Recommended Feature Set

- Time domain: mean, std, rms, peak, peak_to_peak, crest_factor, skewness, kurtosis.
- Frequency domain: dominant_frequency_hz, spectral_centroid_hz, spectral_energy, spectral_entropy.
- Channels: vibration_1, phase_current_1, phase_current_2.
- Outliers remain in the data unless independent sensor-error evidence is found.

## Recommended Split

- Provisional: stratified group split with `group=measurement_id`, fixed `random_state=42`.
- Required guard: `assert_no_group_leakage` must pass before model fitting.
- Re-evaluate bearing-group splitting after more healthy bearing archives are acquired.

## STEP 04 Input Specification

- One row per 1.0-second, non-overlapping window.
- Preserve measurement ID, bearing ID, operating condition, state, window ID, and sample bounds.
- Do not treat the 2:1 class ratio as independent-window evidence or automatically apply SMOTE.
- Fit any scaler only on the training split; Random Forest does not require scaling.

## Known Limitations

- Only 3 of 32 bearing-state archives are local, including only one healthy bearing.
- Bearing identity and state are confounded in the current subset.
- Effects and plots are exploratory and must not be reported as model accuracy.
- Physical units are absent in the MAT signal metadata.
