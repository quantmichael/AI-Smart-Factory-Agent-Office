import numpy as np
import pytest

from app.ml.features.time_domain import time_domain_features


def test_known_rms_and_peak_features() -> None:
    result = time_domain_features(np.array([3.0, 4.0]))

    assert result["rms"] == pytest.approx(np.sqrt(12.5))
    assert result["peak"] == 4.0
    assert result["peak_to_peak"] == 1.0


def test_zero_signal_has_safe_ratios_and_moments() -> None:
    result = time_domain_features(np.zeros(16))

    assert result["rms"] == 0.0
    assert result["crest_factor"] == 0.0
    assert result["skewness"] == 0.0
    assert result["kurtosis"] == 0.0


def test_non_finite_signal_is_rejected() -> None:
    with pytest.raises(ValueError, match="NaN or Inf"):
        time_domain_features(np.array([0.0, np.nan]))
