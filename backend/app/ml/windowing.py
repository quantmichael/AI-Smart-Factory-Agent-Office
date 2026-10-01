"""Leakage-aware signal window definitions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class WindowBounds:
    window_id: str
    start: int
    end: int


def window_bounds(
    sample_count: int,
    sampling_rate_hz: float,
    duration_sec: float,
    overlap: float,
) -> tuple[WindowBounds, ...]:
    if sample_count < 1:
        raise ValueError("sample_count must be positive")
    if sampling_rate_hz <= 0 or duration_sec <= 0:
        raise ValueError("sampling rate and duration must be positive")
    if not 0 <= overlap < 1:
        raise ValueError("overlap must be in [0, 1)")
    window_size = int(round(sampling_rate_hz * duration_sec))
    if window_size < 1:
        raise ValueError("window size rounded to zero samples")
    step = max(1, int(round(window_size * (1.0 - overlap))))
    if sample_count < window_size:
        return ()
    starts = range(0, sample_count - window_size + 1, step)
    return tuple(
        WindowBounds(window_id=f"w{index:03d}", start=start, end=start + window_size)
        for index, start in enumerate(starts)
    )


def iter_signal_windows(
    signal: np.ndarray,
    sampling_rate_hz: float,
    duration_sec: float,
    overlap: float,
):
    values = np.asarray(signal)
    for bounds in window_bounds(values.size, sampling_rate_hz, duration_sec, overlap):
        yield bounds, values[bounds.start : bounds.end]
