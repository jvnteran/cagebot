"""CAGEBOT design system — ported from Claude Design prototype."""

import streamlit as st

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;600;700&family=Exo+2:wght@300;400;500;600&family=Rajdhani:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* === DESIGN TOKENS === */
:root {
    --bg-000: #000000;
    --bg-010: #060606;
    --bg-020: #0b0b0c;
    --bg-030: #131316;
    --bg-040: #1a1a1f;
    --line-1: #1c1c20;
    --line-2: #26262c;
    --line-3: #34343c;
    --ink-100: #f5f5f5;
    --ink-080: #c8c8cf;
    --ink-060: #8e8e96;
    --ink-040: #5a5a62;
    --ink-020: #38383e;
    --red: #dc2626;
    --red-dim: #7c1717;
    --red-bg: rgba(220, 38, 38, 0.08);
}

/* === GLOBAL TYPOGRAPHY === */
html, body, [class*="css"] {
    font-family: 'Exo 2', sans-serif !important;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}
h1, h2, h3, h4, h5, h6 {
    font-family: 'Chakra Petch', sans-serif !important;
    font-weight: 600;
    letter-spacing: 0.02em;
}

/* === SIDEBAR === */
section[data-testid="stSidebar"] {
    background-color: var(--bg-010) !important;
    border-right: 1px solid var(--line-1) !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
    font-family: 'Exo 2', sans-serif;
    font-size: 13px;
}

/* === METRIC CARDS === */
div[data-testid="stMetric"] {
    background-color: var(--bg-010);
    border: 1px solid var(--line-1);
    border-radius: 8px;
    padding: 16px;
}
div[data-testid="stMetric"] label {
    font-family: 'JetBrains Mono', monospace !important;
    color: var(--ink-040) !important;
    font-size: 10px !important;
    text-transform: uppercase;
    letter-spacing: 0.18em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700;
    font-size: 32px !important;
}

/* === EXPANDER === */
details summary {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: var(--ink-060);
    text-transform: uppercase;
    letter-spacing: 0.18em;
}
details summary:hover { color: var(--ink-100); }

/* === DATAFRAME === */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--line-1);
    border-radius: 8px;
}

/* === HEADER === */
header[data-testid="stHeader"] {
    background-color: var(--bg-000) !important;
}

/* === HIDE BRANDING === */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* === CODE BLOCKS === */
code { font-family: 'JetBrains Mono', monospace !important; }
</style>
"""

SIDEBAR_BRAND = (
    "<div style='padding:0 0 8px 0;'>"
    "<span style='font-family:Chakra Petch,sans-serif;font-weight:700;font-size:28px;"
    "letter-spacing:0.04em;color:#ffffff;-webkit-text-stroke:0.5px #ffffff;"
    "text-shadow:0 0 18px rgba(255,255,255,0.25);'>CAGEBOT</span>"
    "<br><span style='font-family:JetBrains Mono,monospace;font-size:9px;"
    "color:#5a5a62;text-transform:uppercase;letter-spacing:0.15em;'>"
    "prediction engine</span></div>"
)

SIDEBAR_STATUS = (
    "<div style='background:#000;border:1px solid #1c1c20;border-radius:6px;"
    "padding:12px;font-family:JetBrains Mono,monospace;font-size:10px;"
    "color:#8e8e96;margin-top:16px;'>"
    "<div style='display:flex;align-items:center;justify-content:space-between;"
    "font-size:9px;letter-spacing:0.2em;color:#5a5a62;text-transform:uppercase;"
    "margin-bottom:10px;'>"
    "<span>// system</span>"
    "<span style='width:6px;height:6px;border-radius:50%;background:#10b981;"
    "box-shadow:0 0 8px #10b981;display:inline-block;'></span></div>"
    "<div style='display:flex;justify-content:space-between;padding:4px 0;"
    "border-bottom:1px dashed #1c1c20;'>"
    "<span style='color:#5a5a62;text-transform:uppercase;letter-spacing:0.1em;'>model</span>"
    "<span style='color:#c8c8cf;'>V2.4</span></div>"
    "<div style='display:flex;justify-content:space-between;padding:4px 0;"
    "border-bottom:1px dashed #1c1c20;'>"
    "<span style='color:#5a5a62;text-transform:uppercase;letter-spacing:0.1em;'>features</span>"
    "<span style='color:#c8c8cf;'>154</span></div>"
    "<div style='display:flex;justify-content:space-between;padding:4px 0;"
    "border-bottom:1px dashed #1c1c20;'>"
    "<span style='color:#5a5a62;text-transform:uppercase;letter-spacing:0.1em;'>vps</span>"
    "<span style='color:#c8c8cf;'>SF03</span></div>"
    "<div style='display:flex;justify-content:space-between;padding:4px 0;'>"
    "<span style='color:#5a5a62;text-transform:uppercase;letter-spacing:0.1em;'>schema</span>"
    "<span style='color:#c8c8cf;'>6 tables</span></div>"
    "</div>"
)


def inject_styles():
    """Call once at the top of each page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.sidebar.markdown(SIDEBAR_BRAND, unsafe_allow_html=True)
    st.sidebar.markdown(SIDEBAR_STATUS, unsafe_allow_html=True)


def eyebrow(system_num: str, label: str):
    """Render a system eyebrow: // SYSTEM 00 · OVERVIEW"""
    st.markdown(
        f"<p style='font-family:JetBrains Mono,monospace;font-size:10px;"
        f"color:#5a5a62;text-transform:uppercase;letter-spacing:0.25em;"
        f"margin-bottom:6px;'>// system {system_num} · {label}</p>",
        unsafe_allow_html=True,
    )


def section_title(title: str):
    """Render a section title in Chakra Petch."""
    st.markdown(
        f"<p style='font-family:Chakra Petch,sans-serif;font-size:14px;"
        f"font-weight:600;letter-spacing:0.18em;text-transform:uppercase;"
        f"color:#f5f5f5;margin-bottom:4px;'>{title}</p>",
        unsafe_allow_html=True,
    )


def hero_number(value: float, label: str, sub: str):
    """Render the hero metric — large number with split decimal."""
    integer = int(value)
    decimal = int(round((value - integer) * 10))
    st.markdown(
        f"""<div style="background:radial-gradient(circle at 0% 100%,rgba(220,38,38,0.08),transparent 60%),
            #060606;border:1px solid #dc2626;border-radius:10px;padding:24px;position:relative;overflow:hidden;">
        <div style="position:absolute;top:0;left:0;right:0;height:2px;
            background:linear-gradient(90deg,#dc2626,transparent);"></div>
        <div style="font-family:JetBrains Mono,monospace;font-size:10px;color:#5a5a62;
            text-transform:uppercase;letter-spacing:0.25em;display:flex;align-items:center;gap:8px;">
            <span style="width:5px;height:5px;background:#dc2626;border-radius:50%;"></span>
            primary metric // {label}</div>
        <div style="font-family:Rajdhani,sans-serif;font-weight:700;line-height:0.95;
            margin:10px 0 4px;display:flex;align-items:baseline;">
            <span style="font-size:64px;color:#f5f5f5;">{integer}</span>
            <span style="font-size:32px;color:#5a5a62;font-weight:500;margin-left:2px;">.{decimal}</span>
            <span style="font-size:22px;color:#5a5a62;margin-left:4px;font-weight:500;">%</span></div>
        <div style="font-family:Chakra Petch,sans-serif;font-size:16px;letter-spacing:0.15em;
            text-transform:uppercase;color:#f5f5f5;">model + override</div>
        <div style="font-family:JetBrains Mono,monospace;font-size:11px;color:#8e8e96;
            margin-top:14px;">{sub}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def stat_card(label: str, value: str, sub: str = ""):
    """Render a secondary stat card."""
    sub_html = (f"<div style='font-family:JetBrains Mono,monospace;font-size:10px;"
                f"color:#5a5a62;margin-top:4px;'>{sub}</div>") if sub else ""
    st.markdown(
        f"""<div style="background:#060606;border:1px solid #1c1c20;border-radius:8px;padding:16px;">
        <div style="font-family:JetBrains Mono,monospace;font-size:10px;color:#5a5a62;
            text-transform:uppercase;letter-spacing:0.18em;">{label}</div>
        <div style="font-family:Rajdhani,sans-serif;font-size:32px;font-weight:600;
            color:#f5f5f5;margin-top:4px;line-height:1;">{value}</div>
        {sub_html}</div>""",
        unsafe_allow_html=True,
    )


def best_call_card(name: str, event: str, model_prob: float, market_prob: float, edge: float):
    """Trading-card style best call with corner brackets."""
    st.markdown(
        f"""<div style="background:#060606;border:1px solid #1c1c20;border-radius:8px;
            padding:16px;position:relative;overflow:hidden;min-height:200px;">
        <div style="position:absolute;top:0;left:0;width:24px;height:24px;
            border-top:1px solid #f5f5f5;border-left:1px solid #f5f5f5;"></div>
        <div style="position:absolute;bottom:0;right:0;width:24px;height:24px;
            border-bottom:1px solid #f5f5f5;border-right:1px solid #f5f5f5;"></div>
        <div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#5a5a62;
            letter-spacing:0.18em;text-transform:uppercase;">{event}</div>
        <div style="font-family:Chakra Petch,sans-serif;font-size:16px;letter-spacing:0.04em;
            text-transform:uppercase;color:#f5f5f5;margin:4px 0 10px;line-height:1.1;">{name}</div>
        <div style="display:flex;justify-content:space-between;font-family:JetBrains Mono,monospace;
            font-size:11px;color:#8e8e96;padding:3px 0;">
            <span>model</span><span style="color:#f5f5f5;">{model_prob}%</span></div>
        <div style="display:flex;justify-content:space-between;font-family:JetBrains Mono,monospace;
            font-size:11px;color:#8e8e96;padding:3px 0;">
            <span>market</span><span style="color:#dc2626;">{market_prob}%</span></div>
        <div style="margin-top:10px;padding:6px 8px;background:rgba(245,245,245,0.06);
            border:1px solid #5a5a62;border-radius:4px;font-family:JetBrains Mono,monospace;
            font-size:11px;color:#f5f5f5;text-align:center;letter-spacing:0.05em;">
            +{edge:.1f}pp edge</div>
        </div>""",
        unsafe_allow_html=True,
    )
