"""Characterize the upstream engine without changing its behavior."""

import hashlib
import math
from pathlib import Path

import pytest

from app.legacy.engine import validate_parcel


def test_upstream_source_is_unchanged():
    source = Path(__file__).parents[1] / "app" / "legacy" / "engine.py"
    content = source.read_bytes()
    blob = b"blob " + str(len(content)).encode() + b"\0" + content
    assert hashlib.sha1(blob, usedforsecurity=False).hexdigest() == (
        "94da2f30964b6123a8bb26bdfa5e67a3e4427503"
    )


def test_matching_measurements():
    result = validate_parcel({"A": 0.0, "B": 0.4}, 100.0, 0, 1.0, 90.0)
    assert result == {
        "status": "VERIFIED",
        "maximum_deviation": 0.4,
        "average_deviation": 0.2,
        "overlap_percentage": 100.0,
        "points_outside": 0,
        "deviation_ok": True,
        "overlap_ok": True,
        "points_ok": True,
    }


@pytest.mark.parametrize(
    ("deviations", "overlap", "outside", "failed_flag"),
    [
        ({"A": 1.01}, 100.0, 0, "deviation_ok"),
        ({"A": 0.0}, 89.99, 0, "overlap_ok"),
        ({"A": 0.0}, 100.0, 1, "points_ok"),
    ],
)
def test_each_rule_independently_rejects(deviations, overlap, outside, failed_flag):
    result = validate_parcel(deviations, overlap, outside, 1.0, 90.0)
    assert result["status"] == "MISMATCH"
    assert result[failed_flag] is False


def test_thresholds_are_inclusive():
    result = validate_parcel({"A": 1.0}, 90.0, 0, 1.0, 90.0)
    assert result["status"] == "VERIFIED"


def test_rules_are_configurable_not_official_tolerances():
    strict = validate_parcel({"A": 0.5}, 95.0, 0, 0.1, 99.0)
    loose = validate_parcel({"A": 0.5}, 95.0, 0, 0.6, 94.0)
    assert strict["status"] == "MISMATCH"
    assert loose["status"] == "VERIFIED"


def test_empty_deviations_preserve_legacy_exception():
    with pytest.raises(ValueError, match="empty"):
        validate_parcel({}, 100.0, 0, 1.0, 90.0)


def test_all_checks_can_fail_together():
    result = validate_parcel({"A": 3.0, "B": 5.0}, 50.0, 2, 1.0, 90.0)
    assert result["status"] == "MISMATCH"
    assert result["maximum_deviation"] == 5.0
    assert result["average_deviation"] == 4.0
    assert not any(result[key] for key in ("deviation_ok", "overlap_ok", "points_ok"))


def test_nonfinite_input_is_not_an_api_validation_contract():
    result = validate_parcel({"A": float("nan")}, 100.0, 0, 1.0, 90.0)
    assert math.isnan(result["maximum_deviation"])
    assert result["status"] == "MISMATCH"
    # An eventual API adapter must reject nonfinite input before invoking this function.
