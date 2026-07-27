"""Extract fights from master_picks.csv, enrich with MOV, load into fights table."""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER_PICKS = ROOT / "data/master/master_picks.csv"
PROCESSED_DIR = ROOT / "data/processed"


def normalize_fight_key(fight_str: str) -> tuple[str, str]:
    """Sort fighter names for order-independent matching."""
    # Handle both "vs" and "vs." separators
    normalized = fight_str.replace(" vs. ", " vs ")
    parts = normalized.split(" vs ")
    if len(parts) != 2:
        return (fight_str.strip().lower(), "")
    a, b = parts[0].strip().lower(), parts[1].strip().lower()
    return tuple(sorted([a, b]))


def parse_mov_prob(val) -> float | None:
    if not val:
        return None
    s = str(val).strip().rstrip("%")
    try:
        return float(s)
    except ValueError:
        return None


def match_mov_to_fight(fight_str: str, mov_lookup: dict) -> dict | None:
    key = normalize_fight_key(fight_str)
    return mov_lookup.get(key)


def load_mov_for_event(event_stem: str) -> dict:
    """Load MOV predictions from per-event _method.csv. Returns {sorted_key: row}."""
    year = event_stem.split("_")[1]
    event_dir = PROCESSED_DIR / year / event_stem
    method_files = list(event_dir.glob("*_method.csv")) if event_dir.exists() else []
    if not method_files:
        return {}
    with open(method_files[0]) as f:
        return {normalize_fight_key(row["fight"]): row for row in csv.DictReader(f)}


def _get_fighter_id(conn, name: str) -> int | None:
    if not name or not name.strip():
        return None
    clean = name.strip().lower()
    cur = conn.cursor()
    # Exact match first
    cur.execute("SELECT id FROM fighters WHERE name = %s", (clean,))
    row = cur.fetchone()
    if row:
        return row[0]
    # Fuzzy fallback: try prefix match (handles "Allen Frye" vs "Allen Frye Jr.")
    cur.execute("SELECT id FROM fighters WHERE name LIKE %s ORDER BY name LIMIT 1",
                (clean + "%",))
    row = cur.fetchone()
    return row[0] if row else None


def _get_event_id(conn, stem: str) -> int | None:
    cur = conn.cursor()
    cur.execute("SELECT id FROM events WHERE stem = %s", (stem,))
    row = cur.fetchone()
    return row[0] if row else None


def load_fights(conn):
    with open(MASTER_PICKS) as f:
        picks = list(csv.DictReader(f))

    # Group by event for MOV lookup
    events_in_picks = set(r["event_stem"] for r in picks)
    mov_by_event = {stem: load_mov_for_event(stem) for stem in events_in_picks}

    inserted = 0
    skipped = 0
    for pick in picks:
        event_id = _get_event_id(conn, pick["event_stem"])
        fa_id = _get_fighter_id(conn, pick["fighter_a"])
        fb_id = _get_fighter_id(conn, pick["fighter_b"])
        pick_id = _get_fighter_id(conn, pick["model_pick"])

        if not all([event_id, fa_id, fb_id, pick_id]):
            skipped += 1
            continue

        winner = pick.get("actual_winner", "").strip()
        winner_id = _get_fighter_id(conn, winner) if winner and winner != "DRAW" else None

        # MOV enrichment
        mov = match_mov_to_fight(pick["fight"], mov_by_event.get(pick["event_stem"], {}))
        predicted_method = mov.get("predicted_method") if mov else None
        ko_prob = parse_mov_prob(mov.get("ko_prob")) if mov else None
        sub_prob = parse_mov_prob(mov.get("sub_prob")) if mov else None
        dec_prob = parse_mov_prob(mov.get("dec_prob")) if mov else None

        finish_round = pick.get("finish_round", "")
        finish_round = int(finish_round) if finish_round else None

        cur = conn.cursor()
        cur.execute("""
            INSERT INTO fights (event_id, fighter_a_id, fighter_b_id, model_pick_id,
                model_prob, predicted_method, ko_prob, sub_prob, dec_prob,
                actual_winner_id, finish_method, finish_round, finish_time)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (event_id, fighter_a_id, fighter_b_id)
            DO UPDATE SET model_pick_id=EXCLUDED.model_pick_id,
                model_prob=EXCLUDED.model_prob, predicted_method=EXCLUDED.predicted_method,
                ko_prob=EXCLUDED.ko_prob, sub_prob=EXCLUDED.sub_prob, dec_prob=EXCLUDED.dec_prob,
                actual_winner_id=EXCLUDED.actual_winner_id, finish_method=EXCLUDED.finish_method,
                finish_round=EXCLUDED.finish_round, finish_time=EXCLUDED.finish_time
        """, (
            event_id, fa_id, fb_id, pick_id,
            float(pick["model_prob"]),
            predicted_method, ko_prob, sub_prob, dec_prob,
            winner_id,
            pick.get("finish_method") or None,
            finish_round,
            pick.get("finish_time") or None,
        ))
        inserted += 1

    print(f"  fights: {inserted} rows upserted ({skipped} skipped)")
    return inserted
