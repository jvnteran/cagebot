"""CAGEBOT Dashboard — Fights page."""

import streamlit as st
import plotly.graph_objects as go

from components.db import run_query, safe_query
from components.styles import inject_styles

inject_styles()

st.markdown("<h2>Fight Predictions</h2>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#888;font-size:14px;'>"
    "Browse every prediction the model has made. Filter by event or result "
    "to explore patterns in what the model gets right and wrong.</p>",
    unsafe_allow_html=True,
)

# Load all fights
with st.spinner("Loading fights..."):
    df = safe_query("""
        SELECT event_name, event_date, fighter_a, fighter_b, model_pick, model_prob,
               opening_odds, edge, actual_winner, model_correct, combined_correct,
               finish_method, source, override_pick
        FROM v_fight_detail
        WHERE actual_winner IS NOT NULL
        ORDER BY event_date DESC, model_prob DESC
    """)

# Filters
col1, col2 = st.columns(2)
with col1:
    events = ["All"] + sorted(df["event_name"].unique().tolist(), reverse=True)
    selected_event = st.selectbox("Event", events)
with col2:
    result_filter = st.selectbox("Result", ["All", "Correct", "Wrong"])

filtered = df.copy()
if selected_event != "All":
    filtered = filtered[filtered["event_name"] == selected_event]
if result_filter == "Correct":
    filtered = filtered[filtered["model_correct"].fillna(False)]
elif result_filter == "Wrong":
    filtered = filtered[~filtered["model_correct"].fillna(True)]

# Summary donut + stats
correct = int(filtered["model_correct"].sum())
wrong = len(filtered) - correct
total = len(filtered)
pct = round(100 * correct / total, 1) if total > 0 else 0

col_chart, col_stats = st.columns([1, 2])
with col_chart:
    fig = go.Figure(data=[go.Pie(
        labels=["Correct", "Wrong"],
        values=[correct, wrong],
        hole=0.65,
        marker=dict(colors=["#22d3ee", "#dc2626"]),
        textinfo="none",
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    )])
    fig.update_layout(
        plot_bgcolor="#0a0a0a", paper_bgcolor="#0a0a0a",
        font=dict(color="#f5f5f5", family="Exo 2"),
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        height=180,
        annotations=[dict(
            text=f"<b>{pct}%</b>",
            x=0.5, y=0.5, font_size=28, font_color="#22d3ee",
            font_family="Rajdhani", showarrow=False,
        )],
    )
    st.plotly_chart(fig, use_container_width=True)

with col_stats:
    st.markdown(
        f"<div style='padding:20px 0;'>"
        f"<p style='color:#888;font-size:14px;margin:0;'>Showing <span style='color:#f5f5f5;'>{total}</span> fights</p>"
        f"<p style='color:#22d3ee;font-size:24px;font-weight:700;font-family:Rajdhani;margin:8px 0;'>"
        f"{correct} correct · {wrong} wrong</p>"
        f"<p style='color:#555;font-size:12px;margin:0;'>"
        f"{'All events' if selected_event == 'All' else selected_event} · "
        f"{result_filter} filter</p></div>",
        unsafe_allow_html=True,
    )

# Display table
display = filtered[["event_name", "fighter_a", "fighter_b", "model_pick", "model_prob",
                     "opening_odds", "edge", "actual_winner", "model_correct", "finish_method"]].copy()
display.columns = ["Event", "Fighter A", "Fighter B", "Pick", "Prob %", "Odds",
                    "Edge", "Winner", "Correct", "Method"]
display["Correct"] = display["Correct"].map({True: "✓", False: "✗"})

st.dataframe(
    display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Prob %": st.column_config.NumberColumn(format="%.1f"),
        "Odds": st.column_config.NumberColumn(format="%.3f"),
        "Edge": st.column_config.NumberColumn(format="%.1f"),
    },
)

with st.expander("🔧 View SQL"):
    st.code("""SELECT event_name, fighter_a, fighter_b, model_pick, model_prob,
       opening_odds, edge, actual_winner, model_correct, finish_method
FROM v_fight_detail
WHERE actual_winner IS NOT NULL
ORDER BY event_date DESC;""", language="sql")
