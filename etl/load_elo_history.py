"""Load fighter_elo_history.csv into fighter_elo_history table."""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ELO_HISTORY = ROOT / "data/external/fighter_elo_history.csv"


def parse_elo_row(row: dict) -> dict:
    return {
        "fighter_name": row["fighter_name"].strip().lower(),
        "event_date": row["event_date"],
        "event_name": row.get("event_name", ""),
        "elo_before": float(row["elo_before"]),
        "elo_after": float(row["elo_after"]),
        "elo_delta": float(row["elo_delta"]),
        "elo_fights": int(row["elo_fights"]),
        "opponent_name": row.get("opponent_name", ""),
        "result": row.get("result", ""),
    }


def load_elo_history(conn):
    if not ELO_HISTORY.exists():
        print("  fighter_elo_history.csv not found — skipping")
        return 0

    with open(ELO_HISTORY) as f:
        raw_rows = list(csv.DictReader(f))

    # Build fighter_id cache
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM fighters")
    fighter_cache = {row[1]: row[0] for row in cur.fetchall()}

    batch = []
    for raw in raw_rows:
        parsed = parse_elo_row(raw)
        fighter_id = fighter_cache.get(parsed["fighter_name"])
        if not fighter_id:
            continue

        batch.append((
            fighter_id, parsed["event_date"], parsed["event_name"],
            parsed["elo_before"], parsed["elo_after"], parsed["elo_delta"],
            parsed["elo_fights"], parsed["opponent_name"], parsed["result"],
        ))

    # Batch insert
    from psycopg2.extras import execute_values
    sql = """
        INSERT INTO fighter_elo_history
            (fighter_id, event_date, event_name, elo_before, elo_after,
             elo_delta, elo_fights, opponent_name, result)
        VALUES %s
        ON CONFLICT (fighter_id, event_date) DO UPDATE SET
            elo_before=EXCLUDED.elo_before, elo_after=EXCLUDED.elo_after,
            elo_delta=EXCLUDED.elo_delta, elo_fights=EXCLUDED.elo_fights,
            opponent_name=EXCLUDED.opponent_name, result=EXCLUDED.result,
            event_name=EXCLUDED.event_name
    """
    execute_values(cur, sql, batch)
    inserted = len(batch)
    print(f"  fighter_elo_history: {inserted} rows upserted")
    return inserted
