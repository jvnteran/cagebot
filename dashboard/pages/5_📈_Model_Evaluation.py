"""CAGEBOT Dashboard — Model Evaluation page."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from components.db import safe_query
from components.styles import inject_styles, eyebrow

inject_styles()

eyebrow("05", "model evaluation")

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
    df = safe_query("""
        SELECT model_prob, model_correct
        FROM v_fight_detail
        WHERE actual_winner IS NOT NULL
          AND finish_method NOT IN ('NC', 'Cancelled', 'DRAW')
          AND model_prob IS NOT NULL
    """)

if df is None:
    st.stop()

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
    auc_color = "#f5f5f5"
    st.markdown(
        f"""<div style="background:#0a0a0a;border:1px solid #222;border-radius:10px;padding:20px;text-align:center;">
        <div style="color:#777;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;">AUC Score</div>
        <div style="color:{auc_color};font-size:40px;font-weight:700;font-family:Rajdhani;">{auc:.3f}</div>
        <div style="color:#999;font-size:12px;">0.5 = random · 1.0 = perfect</div>
        <div style="color:#555;font-size:10px;">Discrimination ability</div></div>""",
        unsafe_allow_html=True,
    )
with col2:
    brier_color = "#f5f5f5"
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
    line=dict(color="#dc2626", width=2.5),
    marker=dict(size=cal_df["count"].clip(upper=30) * 0.8 + 6, color="#dc2626",
                line=dict(width=1, color="#222")),
    hovertemplate=(
        "Predicted: %{x:.1f}%<br>"
        "Actual win rate: %{y:.1f}%<br>"
        "Fights: %{text}<extra></extra>"
    ),
    text=cal_df["count"].astype(str),
))

fig_cal.update_layout(
    plot_bgcolor="#060606", paper_bgcolor="#060606",
    font=dict(color="#f5f5f5", family="Exo 2"),
    xaxis=dict(title="Model Predicted Probability %", gridcolor="#1c1c20", range=[45, 100]),
    yaxis=dict(title="Actual Win Rate %", gridcolor="#1c1c20", range=[30, 100]),
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
        colorscale=[[0, "#ef4444"], [0.35, "#f87171"], [0.5, "#a3a3a3"], [0.7, "#6ee7b7"], [1, "#10b981"]],  # soft red → neutral → green
        cmin=40, cmax=90,
        line=dict(width=1, color="#222"),
    ),
    text=[f"{v:.0f}%  ·  n={n}" for v, n in zip(cal_df["actual_win_rate"] * 100, cal_df["count"])],
    textposition="outside",
    textfont=dict(color="#c8c8cf", size=11, family="JetBrains Mono"),
    hovertemplate="Confidence: %{x}<br>Accuracy: %{y:.1f}%<br>Fights: %{customdata}<extra></extra>",
    customdata=cal_df["count"],
))

fig_conf.add_hline(y=50, line_dash="dash", line_color="#555",
                   annotation_text="Coin flip", annotation_font_color="#555")

fig_conf.update_layout(
    plot_bgcolor="#060606", paper_bgcolor="#060606",
    font=dict(color="#f5f5f5", family="Exo 2"),
    xaxis=dict(title="Model Confidence Bucket", gridcolor="#1c1c20"),
    yaxis=dict(title="Actual Accuracy %", gridcolor="#1c1c20", range=[30, 100]),
    margin=dict(l=50, r=20, t=20, b=50),
    height=350,
    showlegend=False,
)
st.plotly_chart(fig_conf, use_container_width=True)

# --- Confusion Matrix ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Confusion Matrix")
st.markdown(
    "<p style='color:#888;font-size:13px;'>"
    "How does the model perform when picking favorites vs underdogs? "
    "The bottom-left cell — underdog picks that won — is where the model "
    "finds value the market misses.</p>",
    unsafe_allow_html=True,
)

with st.spinner("Loading confusion matrix..."):
    cm_df = safe_query("""
        SELECT
            CASE WHEN os.implied_pct > 50 THEN 'Picked Favorite' ELSE 'Picked Underdog' END AS pick_type,
            CASE WHEN f.actual_winner_id = f.model_pick_id THEN 'Pick Won' ELSE 'Pick Lost' END AS outcome,
            COUNT(*) AS fights
        FROM fights f
        LEFT JOIN odds_snapshots os ON os.fight_id = f.id
            AND os.snapshot_type = 'opening' AND os.bookmaker = 'consensus'
        WHERE f.actual_winner_id IS NOT NULL
          AND f.finish_method NOT IN ('NC', 'Cancelled', 'DRAW')
        GROUP BY 1, 2
    """)

if cm_df is not None and not cm_df.empty:
    cm_pivot = cm_df.pivot(index="pick_type", columns="outcome", values="fights").fillna(0)
    total_cm = cm_pivot.values.sum()

    for col in ["Pick Won", "Pick Lost"]:
        if col not in cm_pivot.columns:
            cm_pivot[col] = 0
    for idx in ["Picked Favorite", "Picked Underdog"]:
        if idx not in cm_pivot.index:
            cm_pivot.loc[idx] = 0

    fav_won = int(cm_pivot.loc["Picked Favorite", "Pick Won"])
    fav_lost = int(cm_pivot.loc["Picked Favorite", "Pick Lost"])
    und_won = int(cm_pivot.loc["Picked Underdog", "Pick Won"])
    und_lost = int(cm_pivot.loc["Picked Underdog", "Pick Lost"])

    fav_pct = round(100 * fav_won / (fav_won + fav_lost), 1) if fav_won + fav_lost > 0 else 0
    und_pct = round(100 * und_won / (und_won + und_lost), 1) if und_won + und_lost > 0 else 0
    fav_won_pct = round(100 * fav_won / total_cm, 1)
    fav_lost_pct = round(100 * fav_lost / total_cm, 1)
    und_won_pct = round(100 * und_won / total_cm, 1)
    und_lost_pct = round(100 * und_lost / total_cm, 1)

    hdr = "font-family:JetBrains Mono,monospace;font-size:12px;color:#f5f5f5;text-transform:uppercase;letter-spacing:0.18em;"
    cell_num = "font-family:Rajdhani,sans-serif;font-size:38px;font-weight:700;line-height:1;"
    cell_pct = "font-family:JetBrains Mono,monospace;font-size:12px;color:#c8c8cf;margin-top:6px;"

    cm_html = (
        f'<div style="display:grid;grid-template-columns:120px 1fr 1fr;gap:0;background:#060606;border:1px solid #1c1c20;border-radius:10px;overflow:hidden;">'
        f'<div style="background:#0b0b0c;padding:16px;border-right:1px solid #1c1c20;border-bottom:1px solid #1c1c20;"></div>'
        f'<div style="background:#0b0b0c;padding:16px;border-right:1px solid #1c1c20;border-bottom:1px solid #1c1c20;{hdr}text-align:center;">Pick Won</div>'
        f'<div style="background:#0b0b0c;padding:16px;border-bottom:1px solid #1c1c20;{hdr}text-align:center;">Pick Lost</div>'
        f'<div style="background:#0b0b0c;padding:16px;border-right:1px solid #1c1c20;border-bottom:1px solid #1c1c20;{hdr}">Favorite</div>'
        f'<div style="padding:24px 16px;border-right:1px solid #1c1c20;border-bottom:1px solid #1c1c20;text-align:center;"><div style="{cell_num}color:#f5f5f5;">{fav_won}</div><div style="{cell_pct}">{fav_won_pct}%</div></div>'
        f'<div style="padding:24px 16px;border-bottom:1px solid #1c1c20;text-align:center;"><div style="{cell_num}color:#dc2626;">{fav_lost}</div><div style="{cell_pct}">{fav_lost_pct}%</div></div>'
        f'<div style="background:#0b0b0c;padding:16px;border-right:1px solid #1c1c20;{hdr}">Underdog</div>'
        f'<div style="padding:24px 16px;border-right:1px solid #1c1c20;text-align:center;position:relative;"><div style="{cell_num}color:#f5f5f5;">{und_won}</div><div style="{cell_pct}">{und_won_pct}%</div><div style="position:absolute;top:8px;right:10px;font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:0.2em;color:#f5f5f5;text-transform:uppercase;">// value zone</div></div>'
        f'<div style="padding:24px 16px;text-align:center;"><div style="{cell_num}color:#dc2626;">{und_lost}</div><div style="{cell_pct}">{und_lost_pct}%</div></div>'
        f'</div>'
        f'<p style="font-family:JetBrains Mono,monospace;color:#5a5a62;font-size:10px;text-align:center;margin-top:8px;">'
        f'Favorite picks: {fav_won}/{fav_won+fav_lost} = {fav_pct}% · Underdog picks: {und_won}/{und_won+und_lost} = {und_pct}%</p>'
    )
    st.markdown(cm_html, unsafe_allow_html=True)

with st.expander("// view sql"):
    st.code("""SELECT model_prob, model_correct
FROM v_fight_detail
WHERE actual_winner IS NOT NULL
  AND finish_method NOT IN ('NC', 'Cancelled', 'DRAW');

-- Calibration and AUC computed in Python from these results.""", language="sql")
