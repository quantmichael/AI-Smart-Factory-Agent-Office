import numpy as np

from app.ml.windowing import iter_signal_windows, window_bounds


def test_window_count_without_overlap() -> None:
    bounds = window_bounds(4_000, 1_000.0, 1.0, 0.0)

    assert len(bounds) == 4
    assert bounds[0].start == 0
    assert bounds[-1].end == 4_000


def test_window_count_with_half_overlap() -> None:
    windows = list(iter_signal_windows(np.zeros(4_000), 1_000.0, 1.0, 0.5))

    assert len(windows) == 7
    assert all(values.size == 1_000 for _, values in windows)
