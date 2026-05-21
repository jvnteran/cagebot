"""CAGEBOT Dashboard — Locations page with spinning globe."""

import streamlit as st

from components.db import run_query, safe_query
from components.styles import inject_styles, eyebrow, section_title
from components.globe import render_globe

inject_styles()

eyebrow("01", "global coverage")

st.markdown("<h2>Accuracy by Location</h2>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#8e8e96;font-size:13px;max-width:720px;'>"
    "Model accuracy across UFC event venues worldwide. The globe rotates automatically — "
    "hover to pause and identify cities. Red markers show venue locations.</p>",
    unsafe_allow_html=True,
)

with st.spinner("Loading location data..."):
    df = safe_query("SELECT * FROM v_accuracy_by_location")

if df is not None and not df.empty:
    # Render the spinning globe
    df = df.rename(columns={"latitude": "lat", "longitude": "lon"})
    points = df.to_dict("records")
    render_globe(points, height=520)

    # Insight callout
    best = df.loc[df["accuracy_pct"].idxmax()]
    worst = df.loc[df["accuracy_pct"].idxmin()]
    st.markdown(
        f"<p style='font-family:JetBrains Mono,monospace;color:#8e8e96;font-size:11px;"
        f"text-align:center;margin-top:8px;'>"
        f"best: <span style='color:#f5f5f5;'>{best.city} ({best.accuracy_pct}%)</span> "
        f"across {int(best.events)} evt · "
        f"worst: <span style='color:#dc2626;'>{worst.city} ({worst.accuracy_pct}%)</span> "
        f"across {int(worst.events)} evt</p>",
        unsafe_allow_html=True,
    )

    # Node index table
    st.markdown("<br>", unsafe_allow_html=True)
    section_title("Node Index")

    display_df = df[["city", "country", "events", "decided_fights", "model_correct", "accuracy_pct"]].copy()
    display_df.columns = ["City", "Country", "Events", "Fights", "Correct", "Accuracy %"]
    display_df = display_df.sort_values("Accuracy %", ascending=False)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    with st.expander("// view sql"):
        st.code("SELECT * FROM v_accuracy_by_location;", language="sql")
else:
    st.info("No location data available.")
