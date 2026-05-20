"""Extract events from master_events.csv, merge venue data, load into events table."""

import csv
from pathlib import Path

from etl.db import upsert_rows

ROOT = Path(__file__).resolve().parents[1]
MASTER_EVENTS = ROOT / "data/master/master_events.csv"
VENUE_LOOKUP = ROOT / "data/reference/event_venues.csv"


def extract_events(rows: list[dict] = None) -> list[dict]:
    if rows is None:
        with open(MASTER_EVENTS) as f:
            rows = list(csv.DictReader(f))
    events = []
    for row in rows:
        events.append({
            "stem": row["event_stem"],
            "name": row["event_name"],
            "date": row["event_date"],
            "status": row.get("status", "upcoming"),
            "model_version": row.get("model_version", ""),
        })
    return events


def load_venue_lookup() -> dict:
    if not VENUE_LOOKUP.exists():
        return {}
    with open(VENUE_LOOKUP) as f:
        return {row["event_stem"]: row for row in csv.DictReader(f)}


def merge_venues(events: list[dict], venues: dict = None) -> list[dict]:
    if venues is None:
        venues = load_venue_lookup()
    for e in events:
        v = venues.get(e["stem"], {})
        e["venue"] = v.get("venue") or None
        e["city"] = v.get("city") or None
        e["state"] = v.get("state") or None
        e["country"] = v.get("country") or None
        lat = v.get("latitude", "")
        lng = v.get("longitude", "")
        e["latitude"] = float(lat) if lat else None
        e["longitude"] = float(lng) if lng else None
    return events


def load_events(conn):
    events = extract_events()
    events = merge_venues(events)

    columns = ["stem", "name", "date", "status", "model_version",
               "venue", "city", "state", "country", "latitude", "longitude"]
    rows = [tuple(e[c] for c in columns) for e in events]

    n = upsert_rows(conn, "events", columns, rows, conflict_columns=["stem"])
    print(f"  events: {n} rows upserted")
    return n
