"""CAGEBOT theme CSS injection for Streamlit."""

import streamlit as st

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;600;700&family=Exo+2:wght@300;400;500;600&family=Rajdhani:wght@400;500;600;700&display=swap');

/* Global font overrides */
html, body, [class*="css"] {
    font-family: 'Exo 2', sans-serif;
}
h1, h2, h3, h4, h5, h6 {
    font-family: 'Chakra Petch', sans-serif !important;
    letter-spacing: 0.5px;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background-color: #0a0a0a;
    border: 1px solid #222;
    border-radius: 10px;
    padding: 16px;
}
div[data-testid="stMetric"] label {
    font-family: 'Exo 2', sans-serif !important;
    color: #777 !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700;
    font-size: 36px !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0a0a0a;
    border-right: 1px solid #222;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
    font-family: 'Exo 2', sans-serif;
}

/* Expander (View SQL) */
details summary {
    font-family: 'Exo 2', sans-serif;
    color: #888;
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    border: 1px solid #222;
    border-radius: 8px;
}

/* Hide Streamlit branding but keep sidebar toggle */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {
    background-color: #000 !important;
}
</style>
"""

SIDEBAR_BRAND = (
    "<h1 style='color:#dc2626;font-family:Chakra Petch;letter-spacing:2px;"
    "font-size:24px;margin-bottom:4px;'>CAGEBOT</h1>"
    "<p style='color:#555;font-size:11px;margin-top:0;'>Autonomous Prediction Engine</p>"
)


def inject_styles():
    """Call once at the top of each page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.sidebar.markdown(SIDEBAR_BRAND, unsafe_allow_html=True)
