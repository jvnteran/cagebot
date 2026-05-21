"""CAGEBOT Dashboard — Locations page."""

import streamlit as st
import plotly.express as px

from components.db import run_query, safe_query
from components.styles import inject_styles, eyebrow

inject_styles()

eyebrow("01", "global coverage")

st.markdown("<h2>Accuracy by Location</h2>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#888;font-size:14px;'>"
    "Model accuracy varies by event location. Hover over each dot to see "
    "city-level performance across all completed events.</p>",
    unsafe_allow_html=True,
)

with st.spinner("Loading map data..."):
    df = safe_query("SELECT * FROM v_accuracy_by_location")

if not df.empty:
    df["label"] = df["city"] + ", " + df["country"]

    fig = px.scatter_mapbox(
        df, lat="latitude", lon="longitude",
        size="events", color="accuracy_pct",
        hover_name="label",
        hover_data={"events": True, "decided_fights": True, "accuracy_pct": ":.1f",
                     "latitude": False, "longitude": False},
        color_continuous_scale=["#dc2626", "#f5f5f5", "#f5f5f5"],
        range_color=[40, 90],
        size_max=25,
        zoom=1,
        mapbox_style="carto-darkmatter",
    )
    fig.update_layout(
        paper_bgcolor="#000", plot_bgcolor="#000",
        font=dict(color="#f5f5f5", family="Exo 2"),
        margin=dict(l=0, r=0, t=10, b=0),
        height=450,
        coloraxis_colorbar=dict(title="Accuracy %"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Insight callout
    best = df.loc[df["accuracy_pct"].idxmax()]
    worst = df.loc[df["accuracy_pct"].idxmin()]
    st.markdown(
        f"<p style='color:#888;font-size:13px;'>"
        f"Best: <span style='color:#f5f5f5;'>{best.city} ({best.accuracy_pct}%)</span> "
        f"across {int(best.events)} event(s) · "
        f"Worst: <span style='color:#dc2626;'>{worst.city} ({worst.accuracy_pct}%)</span> "
        f"across {int(worst.events)} event(s)</p>",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    display_df = df[["city", "country", "events", "decided_fights", "model_correct", "accuracy_pct"]].copy()
    display_df.columns = ["City", "Country", "Events", "Fights", "Correct", "Accuracy %"]
    display_df = display_df.sort_values("Accuracy %", ascending=False)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    with st.expander("🔧 View SQL"):
        st.code("SELECT * FROM v_accuracy_by_location;", language="sql")
else:
    st.info("No location data available. Ensure events have venue coordinates.")
