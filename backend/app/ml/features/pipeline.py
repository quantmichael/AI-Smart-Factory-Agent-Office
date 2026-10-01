"""Composed feature extraction used by profiling and future baselines."""

from __future__ import annotations

import numpy as np

from app.ml.features.frequency_domain import frequency_domain_features
from app.ml.features.time_domain import time_domain_features


def extract_signal_features(
    signal: np.ndarray,
    sampling_rate_hz: float,
    *,
    include_frequency: bool = True,
) -> dict[str, float]:
    features = time_domain_features(signal)
    if include_frequency:
        features.update(frequency_domain_features(signal, sampling_rate_hz))
    return features
