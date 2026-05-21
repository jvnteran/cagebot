"""CAGEBOT Dashboard — Fighters page."""

import streamlit as st
import plotly.graph_objects as go

from components.db import run_query, safe_query
from components.styles import inject_styles, eyebrow

inject_styles()

eyebrow("02", "fighter registry")

st.markdown("<h2>Fighter Lookup</h2>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#888;font-size:14px;'>"
    "Search any UFC fighter to see their ELO rating trajectory across their "
    "full career. Cyan dots are wins, red dots are losses.</p>",
    unsafe_allow_html=True,
)

# Fighter dropdown
with st.spinner("Loading fighters..."):
    fighters_df = safe_query("""
        SELECT name, current_elo, elo_fights, stance, height_in, reach_in, last_fight_date
        FROM v_fighter_current
        ORDER BY current_elo DESC
    """)

fighter_names = fighters_df["name"].tolist()
default_idx = fighter_names.index("islam makhachev") if "islam makhachev" in fighter_names else 0
selected = st.selectbox("Search fighter", fighter_names, index=default_idx)

fighter = fighters_df[fighters_df["name"] == selected].iloc[0]

# Info cards
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("ELO", f"{fighter.current_elo:.0f}")
with col2:
    st.metric("Fights", int(fighter.elo_fights))
with col3:
    st.metric("Stance", fighter.stance or "N/A")
with col4:
    if fighter.height_in:
        ft = int(fighter.height_in // 12)
        inch = int(fighter.height_in % 12)
        st.metric("Height", f"{ft}'{inch}\"")
    else:
        st.metric("Height", "N/A")
with col5:
    st.metric("Reach", f"{fighter.reach_in:.0f} in" if fighter.reach_in else "N/A")

st.markdown("<br>", unsafe_allow_html=True)

# ELO trajectory chart
with st.spinner("Loading ELO history..."):
    elo_df = safe_query("""
        SELECT h.event_date, h.event_name, h.elo_before, h.elo_after, h.elo_delta,
               h.opponent_name, h.result, h.elo_fights
        FROM fighter_elo_history h
        JOIN fighters f ON h.fighter_id = f.id
        WHERE f.name = %s
        ORDER BY h.event_date
    """, (selected,))

if not elo_df.empty:
    colors = ["#f5f5f5" if r == "win" else "#dc2626" if r == "loss" else "#888"
              for r in elo_df["result"]]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=elo_df["event_date"], y=elo_df["elo_after"],
        mode="lines+markers", name="ELO",
        line=dict(color="#f5f5f5", width=2),
        marker=dict(size=9, color=colors, line=dict(width=1, color="#222")),
        hovertemplate="%{text}<extra></extra>",
        text=[f"{r.event_name}<br>vs {r.opponent_name} ({r.result})<br>ELO: {r.elo_after:.0f} (Δ {r.elo_delta:+.1f})"
              for _, r in elo_df.iterrows()],
    ))
    fig.add_hline(y=1500, line_dash="dash", line_color="#555",
                  annotation_text="Starting ELO (1500)",
                  annotation_font_color="#555")
    fig.update_layout(
        title=f"ELO Trajectory — {selected.title()}",
        plot_bgcolor="#060606", paper_bgcolor="#060606",
        font=dict(color="#f5f5f5", family="Exo 2"),
        xaxis=dict(gridcolor="#1c1c20", title=""),
        yaxis=dict(gridcolor="#1c1c20", title="ELO Rating"),
        margin=dict(l=40, r=20, t=60, b=40),
        height=400,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Fight history table
    st.markdown("### Fight History")
    history = elo_df[["event_date", "event_name", "opponent_name", "result", "elo_before", "elo_after", "elo_delta"]].copy()
    history.columns = ["Date", "Event", "Opponent", "Result", "ELO Before", "ELO After", "Delta"]
    history = history.sort_values("Date", ascending=False)
    st.dataframe(history, use_container_width=True, hide_index=True)

    with st.expander("🔧 View SQL"):
        st.code(f"""SELECT h.event_date, h.event_name, h.elo_before, h.elo_after,
       h.elo_delta, h.opponent_name, h.result
FROM fighter_elo_history h
JOIN fighters f ON h.fighter_id = f.id
WHERE f.name = '{selected}'
ORDER BY h.event_date;""", language="sql")
else:
    st.info("No ELO history available for this fighter.")
