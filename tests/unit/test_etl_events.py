"""Tests for events ETL loader — pure transformation logic."""
from etl.load_events import extract_events, merge_venues


def test_extract_events_from_csv_rows():
    rows = [
        {"event_stem": "UFC_2026_04_11", "event_name": "UFC 327: Prochazka vs. Ulberg",
         "event_date": "2026-04-11", "model_version": "V2.4", "status": "completed"},
    ]
    events = extract_events(rows)
    assert len(events) == 1
    assert events[0]["stem"] == "UFC_2026_04_11"
    assert events[0]["status"] == "completed"


def test_merge_venues_adds_location():
    events = [{"stem": "UFC_2026_04_11", "name": "UFC 327", "date": "2026-04-11",
               "status": "completed", "model_version": "V2.4"}]
    venues = {"UFC_2026_04_11": {"venue": "T-Mobile Arena", "city": "Las Vegas",
              "state": "Nevada", "country": "United States",
              "latitude": "36.1699", "longitude": "-115.1398"}}
    merged = merge_venues(events, venues)
    assert merged[0]["venue"] == "T-Mobile Arena"
    assert merged[0]["latitude"] == 36.1699


def test_merge_venues_handles_missing():
    events = [{"stem": "UFC_UNKNOWN", "name": "Test", "date": "2026-01-01",
               "status": "upcoming", "model_version": "V2.4"}]
    merged = merge_venues(events, {})
    assert merged[0]["venue"] is None
