"""CAGEBOT Dashboard — Model Evaluation page."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from components.db import run_query
from components.styles import inject_styles

inject_styles()

st.markdown("<h2>Model Evaluation</h2>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#888;font-size:14px;'>"
    "How well does the model actually work? Beyond accuracy, these metrics "
    "measure calibration (does 70% confidence mean 70% win rate?), discrimination "
    "(can the model separate winners from losers?), and reliability (does higher "
    "confidence mean better predictions?).</p>",
    unsafe_allow_html=True,
)

# --- Load data ---
with st.spinner("Loading evaluation data..."):
    df = run_query("""
        SELECT model_prob, model_correct
        FROM v_fight_detail
        WHERE actual_winner IS NOT NULL
          AND finish_method NOT IN ('NC', 'Cancelled', 'DRAW')
          AND model_prob IS NOT NULL
    """)

df["model_correct_int"] = df["model_correct"].astype(int)
total_fights = len(df)

# --- Headline ML metrics ---
# AUC: area under ROC curve
probs = df["model_prob"].values / 100.0
actuals = df["model_correct_int"].values

# Manual AUC computation (avoid sklearn dependency)
# Sort by predicted probability descending
order = np.argsort(-probs)
sorted_actuals = actuals[order]
n_pos = sorted_actuals.sum()
n_neg = total_fights - n_pos
if n_pos > 0 and n_neg > 0:
    tpr_sum = 0
    fp_count = 0
    auc = 0.0
    for i in range(total_fights):
        if sorted_actuals[i] == 1:
            auc += fp_count
            tpr_sum += 1
        else:
            fp_count += 1
    auc = 1.0 - (auc / (n_pos * n_neg))
else:
    auc = 0.5

# Brier score: mean squared error of probabilities
brier = np.mean((probs - actuals) ** 2)

col1, col2, col3 = st.columns(3)
with col1:
    auc_color = "#22d3ee" if auc >= 0.65 else "#f5f5f5"
    st.markdown(
        f"""<div style="background:#0a0a0a;border:1px solid #222;border-radius:10px;padding:20px;text-align:center;">
        <div style="color:#777;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;">AUC Score</div>
        <div style="color:{auc_color};font-size:40px;font-weight:700;font-family:Rajdhani;">{auc:.3f}</div>
        <div style="color:#999;font-size:12px;">0.5 = random · 1.0 = perfect</div>
        <div style="color:#555;font-size:10px;">Discrimination ability</div></div>""",
        unsafe_allow_html=True,
    )
with col2:
    brier_color = "#22d3ee" if brier < 0.22 else "#f5f5f5"
    st.markdown(
        f"""<div style="background:#0a0a0a;border:1px solid #222;border-radius:10px;padding:20px;text-align:center;">
        <div style="color:#777;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;">Brier Score</div>
        <div style="color:{brier_color};font-size:40px;font-weight:700;font-family:Rajdhani;">{brier:.4f}</div>
        <div style="color:#999;font-size:12px;">0.0 = perfect · 0.25 = coin flip</div>
        <div style="color:#555;font-size:10px;">Calibration quality</div></div>""",
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""<div style="background:#0a0a0a;border:1px solid #222;border-radius:10px;padding:20px;text-align:center;">
        <div style="color:#777;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;">Sample Size</div>
        <div style="color:#f5f5f5;font-size:40px;font-weight:700;font-family:Rajdhani;">{total_fights}</div>
        <div style="color:#999;font-size:12px;">decided fights evaluated</div>
        <div style="color:#555;font-size:10px;">Dec 2025 — May 2026</div></div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# --- Calibration Curve ---
st.markdown("### Calibration Curve")
st.markdown(
    "<p style='color:#888;font-size:13px;'>"
    "A well-calibrated model means its confidence reflects reality. If the model says "
    "70%, the fighter should win ~70% of the time. Points on the diagonal = perfect "
    "calibration.</p>",
    unsafe_allow_html=True,
)

# Create calibration buckets
bins = [50, 55, 60, 65, 70, 75, 80, 85, 100]
labels = ["50-55", "55-60", "60-65", "65-70", "70-75", "75-80", "80-85", "85+"]
df["bucket"] = pd.cut(df["model_prob"], bins=bins, labels=labels, right=False)

cal_df = df.groupby("bucket", observed=True).agg(
    count=("model_correct_int", "count"),
    actual_win_rate=("model_correct_int", "mean"),
    avg_predicted=("model_prob", "mean"),
).reset_index()
cal_df = cal_df[cal_df["count"] >= 3]  # need minimum sample

fig_cal = go.Figure()

# Perfect calibration line
fig_cal.add_trace(go.Scatter(
    x=[50, 100], y=[50, 100],
    mode="lines", name="Perfect calibration",
    line=dict(color="#555", width=1, dash="dash"),
))

# Actual calibration
fig_cal.add_trace(go.Scatter(
    x=cal_df["avg_predicted"],
    y=cal_df["actual_win_rate"] * 100,
    mode="lines+markers", name="CAGEBOT",
    line=dict(color="#22d3ee", width=2.5),
    marker=dict(size=cal_df["count"].clip(upper=30) * 0.8 + 6, color="#22d3ee",
                line=dict(width=1, color="#222")),
    hovertemplate=(
        "Predicted: %{x:.1f}%<br>"
        "Actual win rate: %{y:.1f}%<br>"
        "Fights: %{text}<extra></extra>"
    ),
    text=cal_df["count"].astype(str),
))

fig_cal.update_layout(
    plot_bgcolor="#0a0a0a", paper_bgcolor="#0a0a0a",
    font=dict(color="#f5f5f5", family="Exo 2"),
    xaxis=dict(title="Model Predicted Probability %", gridcolor="#1a1a1a", range=[45, 100]),
    yaxis=dict(title="Actual Win Rate %", gridcolor="#1a1a1a", range=[30, 100]),
    margin=dict(l=50, r=20, t=20, b=50),
    height=380,
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig_cal, use_container_width=True)

st.markdown(
    "<p style='color:#666;font-size:12px;text-align:center;'>"
    "Dot size reflects number of fights in each confidence bucket. "
    "Closer to the diagonal = better calibrated.</p>",
    unsafe_allow_html=True,
)

# --- Accuracy by Confidence ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Accuracy by Confidence")
st.markdown(
    "<p style='color:#888;font-size:13px;'>"
    "Does higher model confidence actually mean better predictions? "
    "If the bars trend upward, the model's confidence is meaningful — not noise.</p>",
    unsafe_allow_html=True,
)

fig_conf = go.Figure()

fig_conf.add_trace(go.Bar(
    x=cal_df["bucket"].astype(str),
    y=cal_df["actual_win_rate"] * 100,
    marker=dict(
        color=cal_df["actual_win_rate"] * 100,
        colorscale=[[0, "#dc2626"], [0.5, "#f5f5f5"], [1, "#22d3ee"]],
        cmin=40, cmax=90,
        line=dict(width=1, color="#222"),
    ),
    text=[f"{v:.0f}% ({n})" for v, n in zip(cal_df["actual_win_rate"] * 100, cal_df["count"])],
    textposition="outside",
    textfont=dict(color="#888", size=11),
    hovertemplate="Confidence: %{x}<br>Accuracy: %{y:.1f}%<br>Fights: %{customdata}<extra></extra>",
    customdata=cal_df["count"],
))

fig_conf.add_hline(y=50, line_dash="dash", line_color="#555",
                   annotation_text="Coin flip", annotation_font_color="#555")

fig_conf.update_layout(
    plot_bgcolor="#0a0a0a", paper_bgcolor="#0a0a0a",
    font=dict(color="#f5f5f5", family="Exo 2"),
    xaxis=dict(title="Model Confidence Bucket", gridcolor="#1a1a1a"),
    yaxis=dict(title="Actual Accuracy %", gridcolor="#1a1a1a", range=[30, 100]),
    margin=dict(l=50, r=20, t=20, b=50),
    height=350,
    showlegend=False,
)
st.plotly_chart(fig_conf, use_container_width=True)

# --- Confidence distribution ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Prediction Confidence Distribution")
st.markdown(
    "<p style='color:#888;font-size:13px;'>"
    "How confident is the model across all predictions? A model that always outputs "
    "50-55% isn't useful. A model that spreads its confidence shows it's learning "
    "meaningful patterns.</p>",
    unsafe_allow_html=True,
)

fig_dist = go.Figure()

correct_probs = df[df["model_correct_int"] == 1]["model_prob"]
wrong_probs = df[df["model_correct_int"] == 0]["model_prob"]

fig_dist.add_trace(go.Histogram(
    x=correct_probs, name="Correct",
    marker_color="#22d3ee", opacity=0.7,
    xbins=dict(start=50, end=100, size=5),
))
fig_dist.add_trace(go.Histogram(
    x=wrong_probs, name="Wrong",
    marker_color="#dc2626", opacity=0.7,
    xbins=dict(start=50, end=100, size=5),
))

fig_dist.update_layout(
    barmode="overlay",
    plot_bgcolor="#0a0a0a", paper_bgcolor="#0a0a0a",
    font=dict(color="#f5f5f5", family="Exo 2"),
    xaxis=dict(title="Model Confidence %", gridcolor="#1a1a1a"),
    yaxis=dict(title="Number of Fights", gridcolor="#1a1a1a"),
    margin=dict(l=50, r=20, t=20, b=50),
    height=300,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig_dist, use_container_width=True)

st.markdown(
    "<p style='color:#666;font-size:12px;text-align:center;'>"
    "Cyan = model was correct, red = model was wrong. Ideally, correct predictions "
    "cluster at high confidence and wrong predictions cluster at low confidence.</p>",
    unsafe_allow_html=True,
)

with st.expander("🔧 View SQL"):
    st.code("""SELECT model_prob, model_correct
FROM v_fight_detail
WHERE actual_winner IS NOT NULL
  AND finish_method NOT IN ('NC', 'Cancelled', 'DRAW');

-- Calibration and AUC computed in Python from these results.""", language="sql")
