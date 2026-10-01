"""Small, explicit time-domain feature set for condition monitoring."""

from __future__ import annotations

import numpy as np
from scipy.stats import kurtosis, skew


def _validated_signal(signal: np.ndarray) -> np.ndarray:
    values = np.asarray(signal, dtype=np.float64)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("signal must be a non-empty one-dimensional array")
    if not np.isfinite(values).all():
        raise ValueError("signal contains NaN or Inf")
    return values


def time_domain_features(signal: np.ndarray) -> dict[str, float]:
    """Calculate the STEP 03 baseline time-domain features.

    RMS = sqrt(mean(x²)); Peak = max(abs(x)); Peak-to-peak = max(x)-min(x);
    Crest factor = Peak/RMS. Constant/zero signals use zero for undefined
    standardized moments and safe ratios.
    """

    values = _validated_signal(signal)
    mean = float(np.mean(values))
    standard_deviation = float(np.std(values, ddof=0))
    rms = float(np.sqrt(np.mean(np.square(values))))
    peak = float(np.max(np.abs(values)))
    peak_to_peak = float(np.ptp(values))
    crest_factor = peak / rms if rms > 0 else 0.0
    if standard_deviation == 0.0:
        skewness = 0.0
        excess_kurtosis = 0.0
    else:
        skewness = float(skew(values, bias=False))
        excess_kurtosis = float(kurtosis(values, fisher=True, bias=False))
    return {
        "mean": mean,
        "std": standard_deviation,
        "rms": rms,
        "peak": peak,
        "peak_to_peak": peak_to_peak,
        "crest_factor": float(crest_factor),
        "skewness": skewness,
        "kurtosis": excess_kurtosis,
    }
