"""Database connection for Streamlit dashboard."""

import streamlit as st
import psycopg2
import pandas as pd


def _connect():
    """Create a fresh database connection."""
    return psycopg2.connect(st.secrets["DATABASE_URL"])


def run_query(sql: str, params: tuple = None) -> pd.DataFrame:
    """Execute SQL and return a DataFrame. Handles stale connections from Neon.tech cold starts."""
    if "db_conn" not in st.session_state or st.session_state.db_conn.closed:
        st.session_state.db_conn = _connect()

    conn = st.session_state.db_conn
    try:
        return pd.read_sql_query(sql, conn, params=params)
    except Exception:
        # Connection went stale (Neon.tech idle timeout) — reconnect
        try:
            conn.close()
        except Exception:
            pass
        st.session_state.db_conn = _connect()
        return pd.read_sql_query(sql, st.session_state.db_conn, params=params)
