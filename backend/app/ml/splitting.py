"""Group leakage guards shared by future evaluation pipelines."""

from __future__ import annotations

from collections.abc import Iterable


class GroupLeakageError(ValueError):
    """Raised when a group is present on both sides of an evaluation split."""


def assert_no_group_leakage(
    train_groups: Iterable[str],
    test_groups: Iterable[str],
) -> None:
    overlap = set(train_groups).intersection(test_groups)
    if overlap:
        preview = ", ".join(sorted(overlap)[:5])
        raise GroupLeakageError(f"group leakage detected: {preview}")
