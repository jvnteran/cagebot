"""Tests for fights ETL — name normalization, MOV matching."""
from etl.load_fights import normalize_fight_key, parse_mov_prob, match_mov_to_fight


def test_normalize_fight_key_sorts_names():
    assert normalize_fight_key("Carlos Ulberg vs Jiri Prochazka") == ("carlos ulberg", "jiri prochazka")
    # Method CSV has reversed order
    assert normalize_fight_key("Jiri Prochazka vs Carlos Ulberg") == ("carlos ulberg", "jiri prochazka")


def test_normalize_fight_key_handles_vs_period():
    # Override files use "vs." with period
    assert normalize_fight_key("Grant Dawson vs. Manuel Torres") == ("grant dawson", "manuel torres")
    assert normalize_fight_key("Grant Dawson vs Manuel Torres") == ("grant dawson", "manuel torres")


def test_parse_mov_prob_strips_percent():
    assert parse_mov_prob("54%") == 54.0
    assert parse_mov_prob("30%") == 30.0
    assert parse_mov_prob("") is None
    assert parse_mov_prob(None) is None


def test_match_mov_finds_reversed_order():
    mov_rows = [
        {"fight": "Jiri Prochazka vs Carlos Ulberg", "predicted_method": "KO/TKO",
         "ko_prob": "65%", "sub_prob": "10%", "dec_prob": "25%"},
    ]
    mov_lookup = {normalize_fight_key(r["fight"]): r for r in mov_rows}
    result = match_mov_to_fight("Carlos Ulberg vs Jiri Prochazka", mov_lookup)
    assert result is not None
    assert result["predicted_method"] == "KO/TKO"
