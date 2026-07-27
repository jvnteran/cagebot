"""Tests for odds ETL — pivot from columns to rows."""
from etl.load_odds import pivot_odds_row


def test_pivot_creates_two_rows():
    row = {
        "opening_odds": "1.925", "opening_implied_pct": "51.94",
        "closing_odds": "2.078", "closing_implied_pct": "48.12",
    }
    snapshots = pivot_odds_row(row)
    assert len(snapshots) == 2
    assert snapshots[0]["snapshot_type"] == "opening"
    assert snapshots[0]["odds"] == 1.925
    assert snapshots[1]["snapshot_type"] == "closing"


def test_pivot_skips_empty_closing():
    row = {
        "opening_odds": "1.925", "opening_implied_pct": "51.94",
        "closing_odds": "", "closing_implied_pct": "",
    }
    snapshots = pivot_odds_row(row)
    assert len(snapshots) == 1
    assert snapshots[0]["snapshot_type"] == "opening"


def test_pivot_skips_empty_opening():
    row = {"opening_odds": "", "opening_implied_pct": "", "closing_odds": "", "closing_implied_pct": ""}
    snapshots = pivot_odds_row(row)
    assert len(snapshots) == 0
