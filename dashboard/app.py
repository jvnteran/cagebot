"""CAGEBOT Dashboard — Overview page."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from components.db import safe_query
from components.styles import inject_styles, eyebrow, stat_card, best_call_card, section_title

st.set_page_config(
    page_title="CAGEBOT — Overview",
    page_icon="🥊",
    layout="wide",
    initial_sidebar_state="expanded",
)



inject_styles()

# --- Header ---
eyebrow("00", "overview")

st.markdown("<h2 style='margin-bottom:0;font-size:28px;'>Autonomous UFC Prediction Engine</h2>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#8e8e96;font-size:13px;margin-top:8px;line-height:1.7;max-width:720px;'>"
    "CAGEBOT is a production machine learning system that predicts UFC fight outcomes — "
    "built from scratch, deployed on a DigitalOcean VPS, and running autonomously since "
    "December 2025. It combines an XGBoost model trained on 154 features with a founder "
    "override layer that applies scenario-based reasoning to correct the model on select "
    "fights.</p>",
    unsafe_allow_html=True,
)

# --- Architecture ---
st.markdown(
    "<div style='background:#060606;border:1px solid #1c1c20;border-radius:10px;"
    "overflow:hidden;margin:16px 0 28px;display:grid;grid-template-columns:repeat(4,1fr);'>"
    # Data Ingestion
    "<div style='padding:18px;border-right:1px solid #1c1c20;position:relative;'>"
    "<div style='font-family:Chakra Petch,sans-serif;font-size:12px;letter-spacing:0.18em;"
    "text-transform:uppercase;color:#f5f5f5;margin-bottom:12px;'>Data Ingestion</div>"
    "<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#c8c8cf;"
    "padding:5px 0 5px 12px;border-left:1px solid #26262c;'>TheOddsAPI · 5 books</div>"
    "<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#c8c8cf;"
    "padding:5px 0 5px 12px;border-left:1px solid #26262c;'>UFCStats</div>"
    "<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#c8c8cf;"
    "padding:5px 0 5px 12px;border-left:1px solid #26262c;'>ESPN Profiles</div>"
    "<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#c8c8cf;"
    "padding:5px 0 5px 12px;border-left:1px solid #26262c;'>ELO System</div>"
    "<div style='position:absolute;right:-7px;top:36px;width:14px;height:14px;"
    "background:#060606;border:1px solid #dc2626;border-radius:50%;display:grid;"
    "place-items:center;z-index:2;color:#dc2626;font-family:JetBrains Mono;font-size:10px;'>→</div>"
    "</div>"
    # Prediction
    "<div style='padding:18px;border-right:1px solid #1c1c20;position:relative;'>"
    "<div style='font-family:Chakra Petch,sans-serif;font-size:12px;letter-spacing:0.18em;"
    "text-transform:uppercase;color:#f5f5f5;margin-bottom:12px;'>Prediction</div>"
    "<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#c8c8cf;"
    "padding:5px 0 5px 12px;border-left:1px solid #26262c;'>XGBoost V2.4</div>"
    "<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#c8c8cf;"
    "padding:5px 0 5px 12px;border-left:1px solid #26262c;'>MOV Model</div>"
    "<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#c8c8cf;"
    "padding:5px 0 5px 12px;border-left:1px solid #26262c;'>Risk Assessment</div>"
    "<div style='position:absolute;right:-7px;top:36px;width:14px;height:14px;"
    "background:#060606;border:1px solid #dc2626;border-radius:50%;display:grid;"
    "place-items:center;z-index:2;color:#dc2626;font-family:JetBrains Mono;font-size:10px;'>→</div>"
    "</div>"
    # Automation
    "<div style='padding:18px;border-right:1px solid #1c1c20;position:relative;'>"
    "<div style='font-family:Chakra Petch,sans-serif;font-size:12px;letter-spacing:0.18em;"
    "text-transform:uppercase;color:#f5f5f5;margin-bottom:12px;'>Automation</div>"
    "<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#c8c8cf;"
    "padding:5px 0 5px 12px;border-left:1px solid #26262c;'>Phase-aware scheduler</div>"
    "<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#c8c8cf;"
    "padding:5px 0 5px 12px;border-left:1px solid #26262c;'>6 agents · VPS cron</div>"
    "<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#c8c8cf;"
    "padding:5px 0 5px 12px;border-left:1px solid #26262c;'>Discord notifications</div>"
    "<div style='position:absolute;right:-7px;top:36px;width:14px;height:14px;"
    "background:#060606;border:1px solid #dc2626;border-radius:50%;display:grid;"
    "place-items:center;z-index:2;color:#dc2626;font-family:JetBrains Mono;font-size:10px;'>→</div>"
    "</div>"
    # Analytics
    "<div style='padding:18px;'>"
    "<div style='font-family:Chakra Petch,sans-serif;font-size:12px;letter-spacing:0.18em;"
    "text-transform:uppercase;color:#f5f5f5;margin-bottom:12px;'>Analytics</div>"
    "<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#c8c8cf;"
    "padding:5px 0 5px 12px;border-left:1px solid #26262c;'>PostgreSQL · 6 tables</div>"
    "<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#c8c8cf;"
    "padding:5px 0 5px 12px;border-left:1px solid #26262c;'>Streamlit dashboard</div>"
    "<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#c8c8cf;"
    "padding:5px 0 5px 12px;border-left:1px solid #26262c;'>ETL pipeline</div>"
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)

# --- Headline metrics ---
with st.spinner("Loading metrics..."):
    metrics = safe_query("""
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

if metrics is None:
    st.stop()

m = metrics.iloc[0]
model_pct = round(100 * m.model_correct / m.decided, 1)
combined_pct = round(100 * m.combined_correct / m.decided, 1)
override_total = int(m.override_count)
override_correct = int(m.override_correct)
override_pct = round(100 * override_correct / override_total, 1) if override_total > 0 else 0

# Metric cards — equal grid
c1, c2, c3, c4 = st.columns(4)
with c1:
    stat_card("combined", f"{combined_pct}%",
              f"{int(m.combined_correct)} / {int(m.decided)} · model + overrides")
with c2:
    stat_card("model only", f"{model_pct}%",
              f"{int(m.model_correct)} / {int(m.decided)} · pure XGBoost")
with c3:
    stat_card("override hit-rate", f"{override_pct}%",
              f"{override_correct} / {override_total} · human-in-loop")
with c4:
    stat_card("events", str(int(m.events)),
              "completed since launch")

# --- Accuracy chart ---
st.markdown("<br>", unsafe_allow_html=True)
section_title("Accuracy Over Time")

with st.spinner("Loading chart..."):
    events_df = safe_query("""
        SELECT name, date, decided_fights, model_correct, combined_correct,
               model_accuracy_pct, combined_accuracy_pct
        FROM v_event_accuracy ORDER BY date
    """)

if events_df is None:
    st.stop()

events_df["cum_model_correct"] = events_df["model_correct"].cumsum()
events_df["cum_decided"] = events_df["decided_fights"].cumsum()
events_df["cum_combined_correct"] = events_df["combined_correct"].cumsum()
events_df["cum_model_pct"] = (100 * events_df["cum_model_correct"] / events_df["cum_decided"]).round(1)
events_df["cum_combined_pct"] = (100 * events_df["cum_combined_correct"] / events_df["cum_decided"]).round(1)

fig = go.Figure()
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
    line=dict(color="#f5f5f5", width=1, dash="dot"),
    marker=dict(size=5, color="#f5f5f5", opacity=0.6),
    hovertemplate="%{text}<br>Combined: %{y}%<extra></extra>",
    text=events_df["name"],
))
fig.add_trace(go.Scatter(
    x=events_df["date"], y=events_df["cum_model_pct"],
    mode="lines", name="Model (cumulative)",
    line=dict(color="#dc2626", width=3),
    hovertemplate="Cumulative Model: %{y}%<extra></extra>",
))
fig.add_trace(go.Scatter(
    x=events_df["date"], y=events_df["cum_combined_pct"],
    mode="lines", name="Combined (cumulative)",
    line=dict(color="#f5f5f5", width=3),
    hovertemplate="Cumulative Combined: %{y}%<extra></extra>",
))
fig.add_hline(y=50, line_dash="dash", line_color="#34343c",
              annotation_text="coin flip (50%)", annotation_font_color="#5a5a62")
fig.update_layout(
    plot_bgcolor="#060606", paper_bgcolor="#060606",
    font=dict(color="#c8c8cf", family="JetBrains Mono", size=10),
    xaxis=dict(gridcolor="#1c1c20", title=""),
    yaxis=dict(gridcolor="#1c1c20", title="", range=[30, 100]),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
    margin=dict(l=40, r=20, t=20, b=40),
    height=380,
)
st.plotly_chart(fig, use_container_width=True)

st.markdown(
    "<p style='font-family:JetBrains Mono,monospace;color:#5a5a62;font-size:10px;text-align:center;'>"
    "dotted = per-event variance · solid = cumulative trend</p>",
    unsafe_allow_html=True,
)

with st.expander("// view sql"):
    st.code("""SELECT name, date, model_accuracy_pct, combined_accuracy_pct
FROM v_event_accuracy ORDER BY date;""", language="sql")

# --- Best Calls ---
st.markdown("<br>", unsafe_allow_html=True)
section_title("Best Calls")
st.markdown(
    "<p style='color:#8e8e96;font-size:12px;font-family:JetBrains Mono,monospace;'>"
    "Contrarian picks — model backed the underdog and was proven right.</p>",
    unsafe_allow_html=True,
)

with st.spinner("Loading..."):
    best_calls = safe_query("""
        SELECT event_name, fighter_a, fighter_b, model_pick, model_prob,
               opening_implied, edge, actual_winner
        FROM v_fight_detail
        WHERE model_correct = true AND edge IS NOT NULL AND edge > 10 AND opening_implied < 50
        ORDER BY edge DESC LIMIT 4
    """)

if best_calls is not None and not best_calls.empty:
    # Render as a single HTML grid for guaranteed equal height
    cards_html = "<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:12px;'>"
    for _, row in best_calls.iterrows():
        market_pct = round(row.opening_implied, 1) if pd.notna(row.opening_implied) else 0
        name = row.model_pick.title()
        event = row.event_name
        cards_html += f"""<div style="background:#060606;border:1px solid #1c1c20;border-radius:8px;
            padding:16px;position:relative;overflow:hidden;display:flex;flex-direction:column;">
        <div style="position:absolute;top:0;left:0;width:24px;height:24px;
            border-top:1px solid #f5f5f5;border-left:1px solid #f5f5f5;"></div>
        <div style="position:absolute;bottom:0;right:0;width:24px;height:24px;
            border-bottom:1px solid #f5f5f5;border-right:1px solid #f5f5f5;"></div>
        <div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#5a5a62;
            letter-spacing:0.18em;text-transform:uppercase;">{event}</div>
        <div style="font-family:Chakra Petch,sans-serif;font-size:16px;letter-spacing:0.04em;
            text-transform:uppercase;color:#f5f5f5;margin:4px 0 10px;line-height:1.1;">{name}</div>
        <div style="flex:1;"></div>
        <div style="display:flex;justify-content:space-between;font-family:JetBrains Mono,monospace;
            font-size:11px;color:#8e8e96;padding:3px 0;">
            <span>model</span><span style="color:#f5f5f5;">{row.model_prob}%</span></div>
        <div style="display:flex;justify-content:space-between;font-family:JetBrains Mono,monospace;
            font-size:11px;color:#8e8e96;padding:3px 0;">
            <span>market</span><span style="color:#dc2626;">{market_pct}%</span></div>
        <div style="margin-top:10px;padding:6px 8px;background:rgba(245,245,245,0.06);
            border:1px solid #5a5a62;border-radius:4px;font-family:JetBrains Mono,monospace;
            font-size:11px;color:#f5f5f5;text-align:center;letter-spacing:0.05em;">
            +{row.edge:.1f}pp edge</div>
        </div>"""
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

# --- Story ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<div style='background:#060606;border:1px solid #1c1c20;border-left:2px solid #dc2626;"
    "border-radius:0 10px 10px 0;padding:24px 28px;'>"
    "<h3 style='font-family:Chakra Petch,sans-serif;font-size:14px;letter-spacing:0.18em;"
    "text-transform:uppercase;color:#f5f5f5;margin-bottom:14px;'>About CAGEBOT</h3>"
    "<p style='font-size:13px;color:#c8c8cf;line-height:1.85;margin:0 0 12px;'>"
    "CAGEBOT was built to answer a straightforward question: can structured data and "
    "machine learning predict UFC fight outcomes better than intuition alone? MMA presents "
    "a unique modeling challenge — small sample sizes, high variance in outcomes, and a "
    "sport where a single moment can override everything the data suggests. This project "
    "treats that challenge as an <span style='color:#f5f5f5;font-weight:500;'>"
    "end-to-end engineering problem</span>, not just a modeling exercise.</p>"
    "<p style='font-size:13px;color:#c8c8cf;line-height:1.85;margin:0 0 12px;'>"
    "The system aggregates market data from multiple sportsbooks, computes custom ELO "
    "ratings across the full UFC roster, and feeds 154 features into an XGBoost classifier "
    "for every fight on each card. A <span style='color:#f5f5f5;font-weight:500;'>"
    "human-in-the-loop override layer</span> then reviews each prediction, applying "
    "scenario-based reasoning to cases where statistical patterns miss context that only "
    "domain knowledge can catch.</p>"
    f"<p style='font-size:13px;color:#c8c8cf;line-height:1.85;margin:0;'>"
    "The entire pipeline — from data ingestion to prediction to results processing — runs "
    "autonomously on a scheduled cadence. Six specialized agents handle tasks like odds "
    f"monitoring, fight-week analysis, and post-event evaluation. After {int(m.decided)} "
    "decided fights across {int(m.events)} events, the data shows that combining ML "
    "predictions with targeted human corrections produces stronger results than either "
    "approach in isolation.</p>"
    "</div>",
    unsafe_allow_html=True,
)
