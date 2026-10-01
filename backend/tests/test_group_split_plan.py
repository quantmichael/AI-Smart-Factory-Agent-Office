import pytest

from app.ml.splitting import GroupLeakageError, assert_no_group_leakage


def test_disjoint_groups_pass() -> None:
    assert_no_group_leakage({"m1", "m2"}, {"m3"})


def test_overlapping_groups_fail() -> None:
    with pytest.raises(GroupLeakageError, match="m2"):
        assert_no_group_leakage({"m1", "m2"}, {"m2", "m3"})
