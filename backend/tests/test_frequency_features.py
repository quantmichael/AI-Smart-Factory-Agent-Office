import numpy as np
import pytest

from app.ml.features.frequency_domain import frequency_domain_features


def test_known_sine_dominant_frequency() -> None:
    sampling_rate = 1_000.0
    time = np.arange(1_000) / sampling_rate
    signal = np.sin(2 * np.pi * 50.0 * time)

    result = frequency_domain_features(signal, sampling_rate)

    assert result["dominant_frequency_hz"] == pytest.approx(50.0, abs=1.0)
    assert 0.0 <= result["spectral_entropy"] <= 1.0


def test_zero_signal_frequency_features_are_zero() -> None:
    assert frequency_domain_features(np.zeros(32), 1_000.0) == {
        "dominant_frequency_hz": 0.0,
        "spectral_centroid_hz": 0.0,
        "spectral_energy": 0.0,
        "spectral_entropy": 0.0,
    }
