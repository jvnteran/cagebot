"""Database connection for Streamlit dashboard."""

import streamlit as st
import psycopg2
import pandas as pd


@st.cache_resource
def get_connection():
    """Return a cached database connection. Streamlit manages lifecycle."""
    return psycopg2.connect(st.secrets["DATABASE_URL"])


def run_query(sql: str, params: tuple = None) -> pd.DataFrame:
    """Execute SQL and return a DataFrame."""
    conn = get_connection()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    except Exception:
        conn.reset()
        return pd.read_sql_query(sql, conn, params=params)
