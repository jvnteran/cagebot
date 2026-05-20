"""Extract overrides from per-event override CSVs, load into overrides table."""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES_DIR = ROOT / "data/raw/overrides"


def filter_actual_overrides(rows: list[dict]) -> list[dict]:
    """Filter to rows with a non-empty override_pick."""
    return [r for r in rows if r.get("override_pick", "").strip()]


def _get_fight_id(conn, event_stem: str, fight_str: str) -> int | None:
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


def _get_fighter_id(conn, name: str) -> int | None:
    cur = conn.cursor()
    cur.execute("SELECT id FROM fighters WHERE name = %s", (name.strip().lower(),))
    row = cur.fetchone()
    return row[0] if row else None


def load_overrides(conn):
    inserted = 0
    for year_dir in sorted(OVERRIDES_DIR.iterdir()):
        if not year_dir.is_dir():
            continue
        for csv_file in sorted(year_dir.glob("*_overrides.csv")):
            event_stem = csv_file.stem.replace("_overrides", "")
            with open(csv_file) as f:
                rows = filter_actual_overrides(list(csv.DictReader(f)))

            for row in rows:
                fight_id = _get_fight_id(conn, event_stem, row["fight"])
                pick_id = _get_fighter_id(conn, row["override_pick"])
                if not fight_id or not pick_id:
                    continue

                notes = row.get("notes", "").strip() or None
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO overrides (fight_id, override_pick_id, notes)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (fight_id) DO UPDATE SET
                        override_pick_id=EXCLUDED.override_pick_id, notes=EXCLUDED.notes
                """, (fight_id, pick_id, notes))
                inserted += 1

    print(f"  overrides: {inserted} rows upserted")
    return inserted
