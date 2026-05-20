"""Tests for fighters ETL loader — pure transformation logic, no DB."""
from etl.load_fighters import extract_fighters_from_picks, extract_fighters_from_fightlogs


def test_extract_fighters_from_picks_lowercases_names():
    rows = [
        {"fighter_a": "Carlos Ulberg", "fighter_b": "Jiri Prochazka", "model_pick": "Carlos Ulberg"},
    ]
    fighters = extract_fighters_from_picks(rows)
    names = [f["name"] for f in fighters]
    assert "carlos ulberg" in names
    assert "jiri prochazka" in names
    assert "Carlos Ulberg" not in names


def test_extract_fighters_deduplicates():
    rows = [
        {"fighter_a": "Carlos Ulberg", "fighter_b": "Jiri Prochazka", "model_pick": "Carlos Ulberg"},
        {"fighter_a": "Carlos Ulberg", "fighter_b": "Paulo Costa", "model_pick": "Carlos Ulberg"},
    ]
    fighters = extract_fighters_from_picks(rows)
    names = [f["name"] for f in fighters]
    assert names.count("carlos ulberg") == 1


def test_extract_fighters_from_fightlogs_gets_physical():
    rows = [
        {"fighter_name": "carlos ulberg", "stance": "Orthodox", "height_in": "75.0",
         "reach_in": "80.0", "dob": "1993-05-17"},
    ]
    lookup = extract_fighters_from_fightlogs(rows)
    assert lookup["carlos ulberg"]["stance"] == "Orthodox"
    assert lookup["carlos ulberg"]["height_in"] == 75.0
