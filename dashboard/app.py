"""CAGEBOT Dashboard — Overview page."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from components.db import run_query
from components.styles import inject_styles

st.set_page_config(
    page_title="CAGEBOT",
    page_icon="🥊",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_styles()

# --- Header ---
st.markdown(
    "<h2 style='margin-bottom:0;'>Autonomous UFC Prediction Engine</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#888;font-size:14px;margin-top:8px;line-height:1.7;'>"
    "CAGEBOT is a production machine learning system that predicts UFC fight outcomes — "
    "built from scratch, deployed on a DigitalOcean VPS, and running autonomously since "
    "December 2025. It combines an XGBoost model trained on 154 features with a founder "
    "override layer that applies scenario-based reasoning to correct the model on select "
    "fights. The system runs a 10-step pre-event pipeline every fight week and an 8-step "
    "post-event pipeline after each card, with 6 autonomous agents handling everything from "
    "odds monitoring to miss analysis.</p>",
    unsafe_allow_html=True,
)

# --- Architecture summary ---
st.markdown(
    "<div style='background:#0a0a0a;border:1px solid #222;border-radius:10px;padding:16px 20px;"
    "margin:12px 0 24px 0;'>"
    "<p style='color:#777;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;'>System Architecture</p>"
    "<p style='color:#ccc;font-size:13px;margin:0;line-height:1.8;'>"
    "<span style='color:#dc2626;'>Data Ingestion</span> → TheOddsAPI (5 sportsbooks) · UFCStats · ESPN Profiles · ELO System<br>"
    "<span style='color:#dc2626;'>Prediction</span> → XGBoost V2.4 (154 features) · Method of Victory Model · Narrative Flag System<br>"
    "<span style='color:#dc2626;'>Automation</span> → Phase-aware scheduler · 6 agents on VPS cron · Discord notifications<br>"
    "<span style='color:#dc2626;'>Analytics</span> → PostgreSQL (6 tables, 4 views) · Streamlit dashboard · ETL pipeline"
    "</p></div>",
    unsafe_allow_html=True,
)

# --- Headline metrics ---
with st.spinner("Loading metrics..."):
    metrics = run_query("""
        SELECT
            COUNT(*) AS decided,
            COUNT(*) FILTER (WHERE f.actual_winner_id = f.model_pick_id) AS model_correct,
            COUNT(ov.id) AS override_count,
            COUNT(ov.id) FILTER (WHERE ov.override_pick_id = f.actual_winner_id) AS override_correct,
            COUNT(*) FILTER (WHERE
                COALESCE(ov.override_pick_id, f.model_pick_id) = f.actual_winner_id
            ) AS combined_correct,
            COUNT(DISTINCT f.event_id) AS events
        FROM fights f
        LEFT JOIN overrides ov ON ov.fight_id = f.id
        WHERE f.actual_winner_id IS NOT NULL
          AND f.finish_method NOT IN ('NC', 'Cancelled', 'DRAW')
    """)

m = metrics.iloc[0]
model_pct = round(100 * m.model_correct / m.decided, 1)
combined_pct = round(100 * m.combined_correct / m.decided, 1)
override_total = int(m.override_count)
override_correct = int(m.override_correct)
override_pct = round(100 * override_correct / override_total, 1) if override_total > 0 else 0
edge_pp = round(combined_pct - 50, 1)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#1a0808,#0a0a0a);border:1px solid #dc2626;
        border-radius:10px;padding:20px;text-align:center;">
        <div style="color:#777;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;">Combined</div>
        <div style="color:#22d3ee;font-size:40px;font-weight:700;font-family:Rajdhani;">{combined_pct}%</div>
        <div style="color:#999;font-size:13px;">{int(m.combined_correct)} / {int(m.decided)}</div>
        <div style="color:#555;font-size:10px;">+{edge_pp}pp above coin flip</div></div>""",
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"""<div style="background:#0a0a0a;border:1px solid #222;border-radius:10px;padding:20px;text-align:center;">
        <div style="color:#777;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;">Model Only</div>
        <div style="color:#f5f5f5;font-size:40px;font-weight:700;font-family:Rajdhani;">{model_pct}%</div>
        <div style="color:#999;font-size:13px;">{int(m.model_correct)} / {int(m.decided)}</div>
        <div style="color:#555;font-size:10px;">Pure XGBoost</div></div>""",
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""<div style="background:#0a0a0a;border:1px solid #222;border-radius:10px;padding:20px;text-align:center;">
        <div style="color:#777;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;">Overrides</div>
        <div style="color:#22d3ee;font-size:40px;font-weight:700;font-family:Rajdhani;">{override_pct}%</div>
        <div style="color:#999;font-size:13px;">{override_correct} / {override_total}</div>
        <div style="color:#555;font-size:10px;">Human-in-the-loop</div></div>""",
        unsafe_allow_html=True,
    )
with col4:
    st.markdown(
        f"""<div style="background:#0a0a0a;border:1px solid #222;border-radius:10px;padding:20px;text-align:center;">
        <div style="color:#777;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;">Events</div>
        <div style="color:#f5f5f5;font-size:40px;font-weight:700;font-family:Rajdhani;">{int(m.events)}</div>
        <div style="color:#999;font-size:13px;">completed</div>
        <div style="color:#555;font-size:10px;">Dec '25 — May '26</div></div>""",
        unsafe_allow_html=True,
    )

# --- Accuracy chart with cumulative line ---
st.markdown("<br>", unsafe_allow_html=True)

with st.spinner("Loading chart..."):
    events_df = run_query("""
        SELECT name, date, decided_fights, model_correct, combined_correct,
               model_accuracy_pct, combined_accuracy_pct
        FROM v_event_accuracy ORDER BY date
    """)

# Compute cumulative accuracy
events_df["cum_model_correct"] = events_df["model_correct"].cumsum()
events_df["cum_decided"] = events_df["decided_fights"].cumsum()
events_df["cum_combined_correct"] = events_df["combined_correct"].cumsum()
events_df["cum_model_pct"] = (100 * events_df["cum_model_correct"] / events_df["cum_decided"]).round(1)
events_df["cum_combined_pct"] = (100 * events_df["cum_combined_correct"] / events_df["cum_decided"]).round(1)

fig = go.Figure()

# Per-event lines (lighter, thinner)
fig.add_trace(go.Scatter(
    x=events_df["date"], y=events_df["model_accuracy_pct"],
    mode="lines+markers", name="Model (per event)",
    line=dict(color="#dc2626", width=1, dash="dot"),
    marker=dict(size=5, color="#dc2626", opacity=0.6),
    hovertemplate="%{text}<br>Model: %{y}%<extra></extra>",
    text=events_df["name"],
))
fig.add_trace(go.Scatter(
    x=events_df["date"], y=events_df["combined_accuracy_pct"],
    mode="lines+markers", name="Combined (per event)",
    line=dict(color="#22d3ee", width=1, dash="dot"),
    marker=dict(size=5, color="#22d3ee", opacity=0.6),
    hovertemplate="%{text}<br>Combined: %{y}%<extra></extra>",
    text=events_df["name"],
))

# Cumulative lines (bold, solid — the real story)
fig.add_trace(go.Scatter(
    x=events_df["date"], y=events_df["cum_model_pct"],
    mode="lines", name="Model (cumulative)",
    line=dict(color="#dc2626", width=3),
    hovertemplate="Cumulative Model: %{y}%<br>After %{text} fights<extra></extra>",
    text=events_df["cum_decided"].astype(str),
))
fig.add_trace(go.Scatter(
    x=events_df["date"], y=events_df["cum_combined_pct"],
    mode="lines", name="Combined (cumulative)",
    line=dict(color="#22d3ee", width=3),
    hovertemplate="Cumulative Combined: %{y}%<br>After %{text} fights<extra></extra>",
    text=events_df["cum_decided"].astype(str),
))

fig.add_hline(y=50, line_dash="dash", line_color="#555",
              annotation_text="Coin flip (50%)", annotation_font_color="#555")
fig.update_layout(
    title="Accuracy Over Time — Per Event vs Cumulative",
    plot_bgcolor="#0a0a0a", paper_bgcolor="#0a0a0a",
    font=dict(color="#f5f5f5", family="Exo 2"),
    xaxis=dict(gridcolor="#1a1a1a", title=""),
    yaxis=dict(gridcolor="#1a1a1a", title="Accuracy %", range=[30, 100]),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(size=10)),
    margin=dict(l=40, r=20, t=60, b=40),
    height=420,
)
st.plotly_chart(fig, use_container_width=True)

st.markdown(
    "<p style='color:#666;font-size:12px;text-align:center;margin-top:-10px;'>"
    "Dotted lines show per-event variance. Solid lines show the cumulative trend converging "
    "as more fights are predicted — the true measure of model reliability.</p>",
    unsafe_allow_html=True,
)

with st.expander("🔧 View SQL"):
    st.code("""SELECT name, date, model_accuracy_pct, combined_accuracy_pct, decided_fights
FROM v_event_accuracy ORDER BY date;""", language="sql")

# --- Best Calls ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Best Calls", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#888;font-size:13px;'>"
    "Fights where the model identified value the market didn't — picked against "
    "the odds and was proven right.</p>",
    unsafe_allow_html=True,
)

with st.spinner("Loading best calls..."):
    best_calls = run_query("""
        SELECT event_name, fighter_a, fighter_b, model_pick, model_prob,
               opening_implied, edge, actual_winner
        FROM v_fight_detail
        WHERE model_correct = true
          AND edge IS NOT NULL AND edge > 10
          AND opening_implied < 50
        ORDER BY edge DESC
        LIMIT 4
    """)

if not best_calls.empty:
    cols = st.columns(len(best_calls))
    for i, (_, row) in enumerate(best_calls.iterrows()):
        with cols[i]:
            market_pct = round(row.opening_implied, 1) if pd.notna(row.opening_implied) else "?"
            st.markdown(
                f"""<div style="background:#0a0a0a;border:1px solid #222;border-radius:10px;padding:16px;text-align:center;">
                <div style="color:#22d3ee;font-size:18px;font-weight:700;font-family:Chakra Petch;margin-bottom:4px;">
                    {row.model_pick.title()}</div>
                <div style="color:#888;font-size:11px;margin-bottom:8px;">{row.event_name}</div>
                <div style="color:#f5f5f5;font-size:13px;">Model: <span style="color:#22d3ee;">{row.model_prob}%</span></div>
                <div style="color:#f5f5f5;font-size:13px;">Market: <span style="color:#dc2626;">{market_pct}%</span></div>
                <div style="color:#22d3ee;font-size:12px;margin-top:6px;">+{round(row.edge, 1)}pp edge ✓</div>
                </div>""",
                unsafe_allow_html=True,
            )

# --- The Story ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<div style='background:#0a0a0a;border-left:3px solid #dc2626;border-radius:0 10px 10px 0;"
    "padding:20px 24px;margin:12px 0;'>"
    "<h3 style='color:#f5f5f5;margin-top:0;font-size:16px;'>The Story Behind CAGEBOT</h3>"
    "<p style='color:#999;font-size:13px;line-height:1.8;margin-bottom:12px;'>"
    "CAGEBOT started as a question: can a machine learning model consistently predict "
    "fight outcomes in the most unpredictable sport on earth? UFC fights are chaotic — "
    "a single punch or submission attempt can end everything in seconds. Most prediction "
    "systems fail because they treat fights like statistics problems. CAGEBOT treats them "
    "like information problems.</p>"
    "<p style='color:#999;font-size:13px;line-height:1.8;margin-bottom:12px;'>"
    "The model ingests 154 features per fight: market odds from 5 sportsbooks, custom ELO "
    "ratings with inactivity decay, striking volume, takedown rates, and last-3-fight recency "
    "metrics. But the real edge comes from the override layer — a human-in-the-loop system "
    "where the founder reviews every prediction and applies scenario elimination to correct "
    "fights where the model's statistical view misses the human element.</p>"
    "<p style='color:#999;font-size:13px;line-height:1.8;margin-bottom:0;'>"
    "The system runs autonomously on a DigitalOcean VPS. A phase-aware scheduler detects "
    "where we are in the fight calendar and dispatches the right pipeline — fetching odds on "
    "Monday, generating predictions by Wednesday, monitoring line movement through Friday, "
    "and processing results on Sunday. Six autonomous agents handle specialized tasks from "
    "ESPN profile scraping to post-event miss analysis. After 6 months and {int(m.decided)} "
    "decided fights, the system has proven that combining ML with domain expertise "
    "consistently outperforms either approach alone.</p>"
    "</div>",
    unsafe_allow_html=True,
)
