"""Load all CSVs into PostgreSQL in FK-dependency order."""

from etl.db import get_conn
from etl.load_fighters import load_fighters
from etl.load_events import load_events
from etl.load_fights import load_fights
from etl.load_odds import load_odds
from etl.load_overrides import load_overrides
from etl.load_elo_history import load_elo_history


def load_all():
    print("=== Loading all CSVs into PostgreSQL ===")
    with get_conn() as conn:
        load_fighters(conn)
        load_events(conn)
        load_fights(conn)
        load_odds(conn)
        load_overrides(conn)
        load_elo_history(conn)
    print("=== Done ===")


if __name__ == "__main__":
    load_all()
