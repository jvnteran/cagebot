"""Tests for overrides ETL — skip empty override_pick rows."""
from etl.load_overrides import filter_actual_overrides


def test_filter_skips_empty_override_pick():
    rows = [
        {"fight": "A vs B", "override_pick": "B", "notes": "test"},
        {"fight": "C vs D", "override_pick": "", "notes": ""},
        {"fight": "E vs F", "override_pick": "F", "notes": "reason"},
    ]
    filtered = filter_actual_overrides(rows)
    assert len(filtered) == 2
    assert filtered[0]["override_pick"] == "B"
    assert filtered[1]["override_pick"] == "F"
