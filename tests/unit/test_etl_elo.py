"""Tests for ELO history ETL."""
from etl.load_elo_history import parse_elo_row


def test_parse_elo_row_converts_types():
    raw = {
        "fighter_name": "carlos ulberg", "event_date": "2026-04-11",
        "event_name": "UFC 327", "elo_before": "1609.1", "elo_after": "1625.1",
        "elo_delta": "16.0", "elo_fights": "11", "opponent_name": "jiri prochazka",
        "result": "win",
    }
    parsed = parse_elo_row(raw)
    assert parsed["fighter_name"] == "carlos ulberg"
    assert parsed["elo_before"] == 1609.1
    assert parsed["elo_after"] == 1625.1
    assert parsed["elo_fights"] == 11


def test_parse_elo_row_handles_first_fight():
    raw = {
        "fighter_name": "nick diaz", "event_date": "2004-04-02",
        "event_name": "UFC 47: It's On!", "elo_before": "1500.0", "elo_after": "1516.0",
        "elo_delta": "16.0", "elo_fights": "1", "opponent_name": "robbie lawler",
        "result": "win",
    }
    parsed = parse_elo_row(raw)
    assert parsed["elo_before"] == 1500.0
