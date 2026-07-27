"""Extract odds from master_odds.csv, pivot columns to rows, load into odds_snapshots."""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER_ODDS = ROOT / "data/master/master_odds.csv"


def _safe_float(val) -> float | None:
    if not val or not str(val).strip():
        return None
    try:
        return float(val)
    except ValueError:
        return None


def pivot_odds_row(row: dict) -> list[dict]:
    """Pivot one master_odds row into 1-2 odds_snapshot dicts."""
    snapshots = []
    opening_odds = _safe_float(row.get("opening_odds"))
    opening_impl = _safe_float(row.get("opening_implied_pct"))
    if opening_odds is not None:
        snapshots.append({
            "snapshot_type": "opening",
            "bookmaker": "consensus",
            "odds": opening_odds,
            "implied_pct": opening_impl,
        })

    closing_odds = _safe_float(row.get("closing_odds"))
    closing_impl = _safe_float(row.get("closing_implied_pct"))
    if closing_odds is not None:
        snapshots.append({
            "snapshot_type": "closing",
            "bookmaker": "consensus",
            "odds": closing_odds,
            "implied_pct": closing_impl,
        })
    return snapshots


def _get_fight_id(conn, event_stem: str, fight_str: str) -> int | None:
    """Look up fight_id by matching event stem + fighter names."""
    from etl.load_fights import normalize_fight_key
    a, b = normalize_fight_key(fight_str)
    cur = conn.cursor()
    cur.execute("""
        SELECT fi.id FROM fights fi
        JOIN events e ON fi.event_id = e.id
        JOIN fighters fa ON fi.fighter_a_id = fa.id
        JOIN fighters fb ON fi.fighter_b_id = fb.id
        WHERE e.stem = %s AND (
            (fa.name = %s AND fb.name = %s) OR (fa.name = %s AND fb.name = %s)
        )
    """, (event_stem, a, b, b, a))
    row = cur.fetchone()
    return row[0] if row else None


def load_odds(conn):
    with open(MASTER_ODDS) as f:
        odds_rows = list(csv.DictReader(f))

    inserted = 0
    for row in odds_rows:
        fight_id = _get_fight_id(conn, row["event_stem"], row["fight"])
        if not fight_id:
            continue

        for snap in pivot_odds_row(row):
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO odds_snapshots (fight_id, bookmaker, odds, implied_pct, snapshot_type)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (fight_id, snapshot_type, bookmaker)
                DO UPDATE SET odds=EXCLUDED.odds, implied_pct=EXCLUDED.implied_pct
            """, (fight_id, snap["bookmaker"], snap["odds"], snap["implied_pct"],
                  snap["snapshot_type"]))
            inserted += 1

    print(f"  odds_snapshots: {inserted} rows upserted")
    return inserted
