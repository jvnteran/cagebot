"""CAGEBOT Dashboard — Market Performance page.

Every query on this page reads sanitized public views, and only in aggregate.
Per-fight staking rows are deliberately not selected or rendered: which fights
the engine acted on, on which side, and at what size are private. All figures
are a simulated record in units — no money staked. Strategy parameters are
intentionally withheld.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.db import safe_query
from components.styles import (
    configure_page, inject_styles, eyebrow, stat_card, section_title,
)

configure_page()
inject_styles()

eyebrow("06", "market performance")

st.markdown("<h2>Market Performance</h2>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#888;font-size:14px;'>"
    "Simulated strategy record &middot; closing-line (CLV) audit &middot; "
    "failure modes. Units only — no money staked.</p>",
    unsafe_allow_html=True,
)

# Aggregate columns only — fight, bet_side and per-row odds stay unselected so
# the individual staking decisions never cross into the public surface.
SQL_RECORD = """SELECT event_date, units, result, pl_units
FROM v_strategy_record_public ORDER BY event_date"""

SQL_AUDIT = """SELECT event_date, model_prob, opening_odds, opening_implied,
       closing_odds, closing_implied, clv_pp, edge, model_correct
FROM v_market_audit"""

with st.spinner("Loading market data..."):
    rec = safe_query(SQL_RECORD)
    audit = safe_query(SQL_AUDIT)

if rec is None or audit is None:
    st.stop()

audit["correct"] = audit["model_correct"].astype(bool)
clv = audit.dropna(subset=["clv_pp"])
pos, neg = clv[clv.clv_pp > 0], clv[clv.clv_pp < 0]

staked = float(rec["units"].sum())
pl = float(rec["pl_units"].sum())
roi = 100 * pl / staked if staked else 0.0
wins = int((rec["result"] == "W").sum())
losses = int((rec["result"] == "L").sum())
dates = pd.to_datetime(rec["event_date"], errors="coerce").dropna()
window = f"{dates.min():%b %Y} — {dates.max():%b %Y}" if not dates.empty else "—"

# Single CSS grid so the four cards are always equal in size and distribution.
_cards = [
    ("strategy roi", f"{roi:+.2f}%",
     f"{pl:+.2f}u on {staked:.2f}u staked · simulated · {window}"),
    ("record", f"{wins}-{losses}",
     f"{len(rec)} settled simulated bets · units only"),
    ("clv → outcome", f"{100 * pos.correct.mean():.1f}%",
     f"win rate when CLV positive (n={len(pos)}) vs "
     f"{100 * neg.correct.mean():.1f}% negative (n={len(neg)})"),
    ("closing-line test", f"{clv.clv_pp.mean():+.2f}pp",
     f"mean CLV · {100 * (clv.clv_pp > 0).mean():.1f}% positive "
     f"(n={len(clv)}) · market efficient"),
]
st.markdown(
    "<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:12px;"
    "align-items:stretch;'>"
    + "".join(
        f"""<div style="background:#060606;border:1px solid #1c1c20;border-radius:8px;
        padding:16px;height:100%;display:flex;flex-direction:column;">
        <div style="font-family:JetBrains Mono,monospace;font-size:10px;color:#5a5a62;
            text-transform:uppercase;letter-spacing:0.18em;">{label}</div>
        <div style="font-family:Rajdhani,sans-serif;font-size:32px;font-weight:600;
            color:#f5f5f5;margin-top:4px;line-height:1;">{value}</div>
        <div style="font-family:JetBrains Mono,monospace;font-size:10px;color:#5a5a62;
            margin-top:4px;">{sub}</div></div>"""
        for label, value, sub in _cards
    )
    + "</div>",
    unsafe_allow_html=True,
)

# --- S1: strategy record + settled bet log ---
st.markdown("<br>", unsafe_allow_html=True)
section_title("Strategy Record — Simulated, Units Only")
st.markdown(
    "<p style='color:#888;font-size:13px;'>"
    "One unified simulated record: every settled stake the strategy engine "
    "produced, graded and summed in units. The engine is selective, "
    "market-gated and fractionally sized — its parameters are withheld.</p>",
    unsafe_allow_html=True,
)

rec_curve = rec.copy()
rec_curve["event_date"] = pd.to_datetime(rec_curve["event_date"], errors="coerce")
rec_curve = rec_curve.dropna(subset=["event_date"]).sort_values("event_date")
rec_curve["cum_pl"] = rec_curve["pl_units"].cumsum().round(2)

fig_eq = go.Figure()
fig_eq.add_trace(go.Scatter(
    x=rec_curve["event_date"], y=rec_curve["cum_pl"],
    mode="lines", name="Cumulative units",
    line=dict(color="#dc2626", width=2.5, shape="hv"),
    hovertemplate="%{x|%Y-%m-%d}<br>Cumulative: %{y:+.2f}u<extra></extra>",
))
fig_eq.add_hline(y=0, line_dash="dash", line_color="#555")
fig_eq.update_layout(
    plot_bgcolor="#060606", paper_bgcolor="#060606",
    font=dict(color="#f5f5f5", family="Exo 2"),
    xaxis=dict(gridcolor="#1c1c20", title=""),
    yaxis=dict(gridcolor="#1c1c20", title="Cumulative P&L (units)"),
    margin=dict(l=50, r=20, t=20, b=40), height=320, showlegend=False,
)
st.plotly_chart(fig_eq, use_container_width=True)

st.markdown(
    "<p style='color:#666;font-size:12px;'>The curve is the whole settled "
    "record summed in order. The individual bets behind it — which fights, "
    "which side, at what size — are not published: those rows are the "
    "strategy, and publishing them would hand over the selection rule the "
    "parameters are withheld to protect.</p>",
    unsafe_allow_html=True,
)

with st.expander("// view sql"):
    st.code(SQL_RECORD + ";", language="sql")

# --- S2: do we beat the closing line? ---
st.markdown("<br>", unsafe_allow_html=True)
section_title("Do We Beat the Closing Line?")
st.markdown(
    "<p style='color:#888;font-size:13px;'>"
    "Closing Line Value (CLV) is the industry-standard skill test: a bettor "
    "who consistently beats the closing price holds real edge. Below, the "
    "same model picks are priced twice — at the opening line and at the "
    "close — on the same paired picks: a pick counts only when both prices "
    "were captured, so the two cards compare like-for-like on an identical "
    "fight count. Closing capture is partial for early months.</p>",
    unsafe_allow_html=True,
)

paired = audit.dropna(subset=["opening_odds", "closing_odds"]).copy()
paired["pl_open"] = np.where(paired.correct, paired.opening_odds - 1.0, -1.0)
paired["pl_close"] = np.where(paired.correct, paired.closing_odds - 1.0, -1.0)

col_a, col_b = st.columns(2)
for col, series, label in ((col_a, paired["pl_open"], "at opening odds"),
                           (col_b, paired["pl_close"], "at closing odds")):
    with col:
        stat_card(f"flat 1u per pick — {label}",
                  f"{series.sum():+.2f}u",
                  f"ROI {100 * series.mean():+.2f}% · n={len(paired)} paired picks")

curves = go.Figure()
_p = paired.copy()
_p["event_date"] = pd.to_datetime(_p["event_date"], errors="coerce")
_p = _p.dropna(subset=["event_date"]).sort_values("event_date")
for colname, name, color in (("pl_open", "Opening", "#8e8e96"),
                             ("pl_close", "Closing", "#dc2626")):
    curves.add_trace(go.Scatter(
        x=_p["event_date"], y=_p[colname].cumsum().round(2), mode="lines", name=name,
        line=dict(color=color, width=2),
        hovertemplate=name + ": %{y:+.2f}u<extra></extra>",
    ))
curves.add_hline(y=0, line_dash="dash", line_color="#555")
curves.update_layout(
    plot_bgcolor="#060606", paper_bgcolor="#060606",
    font=dict(color="#f5f5f5", family="Exo 2"),
    xaxis=dict(gridcolor="#1c1c20", title=""),
    yaxis=dict(gridcolor="#1c1c20", title="Cumulative flat-stake units"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=50, r=20, t=20, b=40), height=320,
)
st.plotly_chart(curves, use_container_width=True)

st.markdown(
    "<p style='color:#c8c8cf;font-size:13px;'><b>Verdict: no — on average the "
    "close absorbs the paper edge.</b> The gap between the two curves is "
    "price discovery doing its job, and measuring it honestly is the point.</p>",
    unsafe_allow_html=True,
)

fig_hist = go.Figure()
fig_hist.add_trace(go.Histogram(
    x=clv["clv_pp"], nbinsx=30, marker=dict(color="#dc2626"),
    hovertemplate="CLV %{x:.2f}pp: %{y} picks<extra></extra>",
))
fig_hist.add_vline(x=float(clv.clv_pp.mean()), line_dash="dash", line_color="#f5f5f5",
                   annotation_text="mean", annotation_font_color="#f5f5f5")
fig_hist.update_layout(
    plot_bgcolor="#060606", paper_bgcolor="#060606",
    font=dict(color="#f5f5f5", family="Exo 2"),
    xaxis=dict(gridcolor="#1c1c20", title="CLV (probability points) per pick"),
    yaxis=dict(gridcolor="#1c1c20", title="Picks"),
    margin=dict(l=50, r=20, t=20, b=40), height=280, showlegend=False,
)
st.plotly_chart(fig_hist, use_container_width=True)

# --- S3: does the closing line know something? ---
st.markdown("<br>", unsafe_allow_html=True)
section_title("Does the Closing Line Know Something?")
st.markdown(
    "<p style='color:#888;font-size:13px;'>"
    "The closing line is the market's final consensus — it aggregates "
    "information (injuries, sharp money, steam) that no single model holds. "
    "If picks the market moved <i>toward</i> win more often than picks it "
    "moved <i>against</i>, the close carries real information.</p>",
    unsafe_allow_html=True,
)

zero = clv[clv.clv_pp == 0]
buckets = [
    ("Market moved toward pick (+CLV)", pos),
    ("No move", zero),
    ("Market moved against pick (−CLV)", neg),
]
fig_clv = go.Figure()
fig_clv.add_trace(go.Bar(
    x=[b[0] for b in buckets],
    y=[100 * b[1].correct.mean() if len(b[1]) else 0 for b in buckets],
    width=0.55,
    marker=dict(color=["#22c55e", "#8e8e96", "#dc2626"], cornerradius=4),
    text=[f"{100 * b[1].correct.mean():.1f}%<br>"
          f"<span style='font-size:10px'>n={len(b[1])}</span>"
          if len(b[1]) else "n=0" for b in buckets],
    textposition="outside",
    textfont=dict(color="#c8c8cf", size=11, family="JetBrains Mono"),
    hovertemplate="%{x}<br>Win rate: %{y:.1f}%<extra></extra>",
))
fig_clv.add_hline(y=50, line_dash="dash", line_color="#555")
fig_clv.update_layout(
    plot_bgcolor="#060606", paper_bgcolor="#060606",
    font=dict(color="#f5f5f5", family="Exo 2"),
    yaxis=dict(gridcolor="#1c1c20", title="Pick win rate %", range=[0, 100]),
    xaxis=dict(gridcolor="#1c1c20", title=""),
    margin=dict(l=50, r=20, t=30, b=40), height=320, showlegend=False,
)
st.plotly_chart(fig_clv, use_container_width=True)

st.markdown(
    f"<p style='color:#c8c8cf;font-size:13px;'><b>Verdict: yes.</b> "
    f"A {100 * pos.correct.mean() - 100 * neg.correct.mean():.0f}-point win-rate "
    "swing the model's own probability doesn't explain. Actionable rule: steam "
    "against a pick is a fade signal.</p>",
    unsafe_allow_html=True,
)

# --- S4: when we disagree with the market, who's right? ---
st.markdown("<br>", unsafe_allow_html=True)
section_title("When We Disagree With the Market, Who's Right?")
st.markdown(
    "<p style='color:#888;font-size:13px;'>"
    "Model edge = model win probability minus the market's implied "
    "probability at open. A calibrated edge should earn money as it grows. "
    "It doesn't — large disagreement usually means the model is the one "
    "that's wrong (miscalibration meeting the favorite-longshot bias).</p>",
    unsafe_allow_html=True,
)

edge_rows = audit.dropna(subset=["edge", "closing_odds"]).copy()
edge_rows["pl"] = np.where(edge_rows.correct, edge_rows.closing_odds - 1.0, -1.0)
edge_rows["bucket"] = pd.cut(
    edge_rows["edge"], [-100, -5, 0, 5, 10, 15, 100],
    labels=["< −5", "−5–0", "0–5", "5–10", "10–15", "15+"])
eg = edge_rows.groupby("bucket", observed=True).agg(
    n=("correct", "size"), acc=("correct", "mean"), units=("pl", "sum"),
).reset_index()

fig_edge = go.Figure()
fig_edge.add_trace(go.Bar(
    x=eg["bucket"].astype(str), y=100 * eg["acc"], width=0.6,
    marker=dict(color="#dc2626", cornerradius=4),
    text=[f"{a:.0f}%<br><span style='font-size:10px'>n={n} · {u:+.2f}u</span>"
          for a, n, u in zip(100 * eg["acc"], eg["n"], eg["units"])],
    textposition="outside",
    textfont=dict(color="#c8c8cf", size=11, family="JetBrains Mono"),
    hovertemplate=("Edge %{x}pp<br>Accuracy %{y:.1f}%<br>"
                   "Flat units: %{customdata:+.2f}u<extra></extra>"),
    customdata=eg["units"].round(2),
))
fig_edge.add_hline(y=50, line_dash="dash", line_color="#555",
                   annotation_text="Coin flip", annotation_font_color="#555")
fig_edge.update_layout(
    plot_bgcolor="#060606", paper_bgcolor="#060606",
    font=dict(color="#f5f5f5", family="Exo 2"),
    xaxis=dict(gridcolor="#1c1c20", title="Model edge vs market (probability points)"),
    yaxis=dict(gridcolor="#1c1c20", title="Pick accuracy %", range=[0, 105]),
    margin=dict(l=50, r=20, t=20, b=50), height=330, showlegend=False,
)
st.plotly_chart(fig_edge, use_container_width=True)

st.markdown(
    "<p style='color:#c8c8cf;font-size:13px;'><b>Verdict: the market.</b> "
    "The strategy treats extreme disagreement as a warning, not an "
    "opportunity — edge caps conviction, it doesn't scale stakes.</p>",
    unsafe_allow_html=True,
)

with st.expander("// view sql "):
    st.code(SQL_AUDIT + ";", language="sql")

# --- S6: where it loses ---
st.markdown("<br>", unsafe_allow_html=True)
section_title("Where It Loses")

edge15 = edge_rows[edge_rows["edge"] >= 15]
brier_rows = audit.dropna(subset=["closing_implied"])
brier_model = float(((brier_rows.model_prob / 100 - brier_rows.correct) ** 2).mean())
brier_close = float(((brier_rows.closing_implied / 100 - brier_rows.correct) ** 2).mean())

rows_html = ""
for title, number, rule in [
    ("No-bet fight profiles",
     "−2% to −17% simulated ROI",
     "Several recurring fight profiles lose money, so the engine sizes them "
     "to zero. Most of the card is a no-bet."),
    ("Extreme-edge picks",
     f"{100 * edge15.correct.mean():.0f}% accuracy, "
     f"{edge15.pl.sum():+.2f}u (n={len(edge15)})" if len(edge15) else "n=0",
     "The model's biggest disagreements with the market perform worst — "
     "edge caps conviction, it never scales stakes."),
    ("Forecast quality vs the close",
     f"Brier {brier_model:.4f} vs {brier_close:.4f} "
     f"(n={len(brier_rows)}, market figure vig-uncorrected)",
     "The closing line remains the better forecaster on the same fights."),
]:
    rows_html += (
        "<div style='display:grid;grid-template-columns:180px 1fr 1.4fr;"
        "gap:12px;padding:12px 0;border-bottom:1px solid #1c1c20;'>"
        f"<div style='font-family:Chakra Petch,sans-serif;font-size:12px;"
        f"letter-spacing:0.1em;text-transform:uppercase;color:#f5f5f5;'>{title}</div>"
        f"<div style='font-family:JetBrains Mono,monospace;font-size:13px;"
        f"color:#dc2626;'>{number}</div>"
        f"<div style='font-size:12px;color:#8e8e96;line-height:1.6;'>{rule}</div>"
        "</div>"
    )

st.markdown(
    "<div style='background:#0a0606;border:1px solid #2a1616;"
    "border-left:2px solid #dc2626;border-radius:0 10px 10px 0;"
    f"padding:8px 24px 4px;'>{rows_html}"
    "<p style='font-size:12px;color:#c8c8cf;padding:12px 0;margin:0;'>"
    "Each of these is why the strategy exists — the rules are the residue "
    "of the failures. Market comparisons use model-only picks throughout.</p>"
    "</div>",
    unsafe_allow_html=True,
)

# --- footer ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<p style='font-family:JetBrains Mono,monospace;color:#5a5a62;"
    "font-size:10px;text-align:center;line-height:1.8;'>"
    "Strategy parameters are withheld by design — "
    "methodology walkthrough available in interview.<br>"
    "Simulated record, units only, no money staked. Decided fights only "
    "(NC / draw / cancelled excluded, same mask as the Model Evaluation "
    "page). Closing-line coverage is partial for early months. Data "
    "refreshes live from the analytics database.</p>",
    unsafe_allow_html=True,
)
