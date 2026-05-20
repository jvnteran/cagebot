"""CAGEBOT Dashboard — SQL Explorer page."""

import streamlit as st

from components.db import run_query
from components.styles import inject_styles
from components.queries import QUERIES

inject_styles()

st.markdown("<h2>SQL Explorer</h2>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#888;font-size:14px;'>"
    "Pre-built queries demonstrating SQL against the CAGEBOT PostgreSQL schema. "
    "Select a query to see the SQL, what it demonstrates, and the live results.</p>",
    unsafe_allow_html=True,
)

query_name = st.selectbox("Select query", list(QUERIES.keys()))
query = QUERIES[query_name]

st.markdown(
    f"<p style='color:#22d3ee;font-size:13px;font-style:italic;'>{query['description']}</p>",
    unsafe_allow_html=True,
)

st.code(query["sql"], language="sql")

st.markdown("#### Results")

with st.spinner("Running query..."):
    try:
        result = run_query(query["sql"])
        st.dataframe(result, use_container_width=True, hide_index=True)
        st.markdown(
            f"<p style='color:#555;font-size:12px;'>{len(result)} rows returned</p>",
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.error(f"Query error: {e}")
