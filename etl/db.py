"""Database connection helper. Reads DATABASE_URL from environment."""

import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import execute_values


def get_connection_string() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        from dotenv import load_dotenv
        load_dotenv()
        url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set in environment or .env")
    return url


@contextmanager
def get_conn():
    conn = psycopg2.connect(get_connection_string())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def upsert_rows(conn, table: str, columns: list[str], rows: list[tuple],
                conflict_columns: list[str]):
    """INSERT ... ON CONFLICT DO UPDATE for a list of rows."""
    if not rows:
        return 0

    cols_str = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    update_cols = [c for c in columns if c not in conflict_columns]
    update_str = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)
    conflict_str = ", ".join(conflict_columns)

    sql = f"""
        INSERT INTO {table} ({cols_str})
        VALUES %s
        ON CONFLICT ({conflict_str}) DO UPDATE SET {update_str}
    """
    template = f"({placeholders})"
    execute_values(conn.cursor(), sql, rows, template=template)
    return len(rows)
