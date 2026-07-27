"""Extract fighter names from master CSVs, load into fighters table."""

import csv
from pathlib import Path

from etl.db import upsert_rows

ROOT = Path(__file__).resolve().parents[1]
MASTER_PICKS = ROOT / "data/master/master_picks.csv"
FIGHTLOGS = ROOT / "data/external/ufcstats_fightlogs_complete.csv"


def extract_fighters_from_picks(rows: list[dict] = None) -> list[dict]:
    """Extract unique fighter names from master_picks rows. Returns list of dicts with 'name'."""
    if rows is None:
        with open(MASTER_PICKS) as f:
            rows = list(csv.DictReader(f))

    seen = set()
    fighters = []
    for row in rows:
        for col in ("fighter_a", "fighter_b"):
            name = row.get(col, "").strip().lower()
            if name and name not in seen:
                seen.add(name)
                fighters.append({"name": name})
    return fighters


def extract_fighters_from_fightlogs(rows: list[dict] = None) -> dict:
    """Extract physical attributes from fightlogs. Returns {name: {stance, height_in, reach_in, dob}}."""
    if rows is None:
        with open(FIGHTLOGS) as f:
            rows = list(csv.DictReader(f))

    lookup = {}
    for row in rows:
        name = row.get("fighter_name", "").strip().lower()
        if not name or name in lookup:
            continue
        height = row.get("height_in", "")
        reach = row.get("reach_in", "")
        lookup[name] = {
            "stance": row.get("stance", "") or None,
            "height_in": float(height) if height else None,
            "reach_in": float(reach) if reach else None,
            "dob": row.get("dob", "") or None,
        }
    return lookup


def load_fighters(conn):
    """Load fighters into DB. Merges picks names with fightlog physical data."""
    fighters = extract_fighters_from_picks()
    physical = extract_fighters_from_fightlogs()

    rows = []
    for f in fighters:
        name = f["name"]
        phys = physical.get(name, {})
        rows.append((
            name,
            phys.get("stance"),
            phys.get("height_in"),
            phys.get("reach_in"),
            phys.get("dob"),
        ))

    # Also add fighters from fightlogs that aren't in picks (for ELO history)
    picks_names = {f["name"] for f in fighters}
    for name, phys in physical.items():
        if name not in picks_names:
            rows.append((name, phys.get("stance"), phys.get("height_in"),
                         phys.get("reach_in"), phys.get("dob")))

    columns = ["name", "stance", "height_in", "reach_in", "dob"]
    n = upsert_rows(conn, "fighters", columns, rows, conflict_columns=["name"])
    print(f"  fighters: {n} rows upserted")
    return n
