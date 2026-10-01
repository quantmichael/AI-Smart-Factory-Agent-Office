"""Bounded frequency-domain features using verified sampling metadata."""

from __future__ import annotations

import numpy as np


def frequency_domain_features(
    signal: np.ndarray,
    sampling_rate_hz: float,
) -> dict[str, float]:
    """Return Hann-windowed spectral descriptors after removing DC.

    Dominant peaks are intentionally reported as spectral peaks, not bearing
    fault frequencies. Spectral entropy is normalized to the range [0, 1].
    """

    values = np.asarray(signal, dtype=np.float64)
    if values.ndim != 1 or values.size < 2:
        raise ValueError("signal must contain at least two samples")
    if not np.isfinite(values).all():
        raise ValueError("signal contains NaN or Inf")
    if not np.isfinite(sampling_rate_hz) or sampling_rate_hz <= 0:
        raise ValueError("sampling_rate_hz must be positive and finite")

    centered = values - np.mean(values)
    window = np.hanning(values.size)
    windowed = centered * window
    spectrum = np.fft.rfft(windowed)
    power = np.square(np.abs(spectrum))
    frequencies = np.fft.rfftfreq(values.size, d=1.0 / sampling_rate_hz)
    if power.size:
        power[0] = 0.0
    total_power = float(np.sum(power))
    if total_power <= 0.0:
        return {
            "dominant_frequency_hz": 0.0,
            "spectral_centroid_hz": 0.0,
            "spectral_energy": 0.0,
            "spectral_entropy": 0.0,
        }

    dominant_index = int(np.argmax(power))
    probabilities = power / total_power
    nonzero = probabilities > 0
    entropy = -float(np.sum(probabilities[nonzero] * np.log(probabilities[nonzero])))
    normalizer = np.log(probabilities.size) if probabilities.size > 1 else 1.0
    window_energy = float(np.sum(np.square(window)))
    spectral_energy = total_power / (values.size * window_energy)
    return {
        "dominant_frequency_hz": float(frequencies[dominant_index]),
        "spectral_centroid_hz": float(np.sum(frequencies * power) / total_power),
        "spectral_energy": float(spectral_energy),
        "spectral_entropy": float(entropy / normalizer),
    }
