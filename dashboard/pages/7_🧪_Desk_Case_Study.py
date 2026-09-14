"""CAGEBOT Dashboard — paper trading desk case study.

A completed engineering case study of two paper market-making sessions, read
from sanitized JSON committed under `dashboard/case_study/`.

COLD START. Nothing on this page touches a database, a credential, an
environment variable or the network. That is not a stylistic preference: this
repository is public, and a page that quietly fell back to a private source
would leak the first time somebody ran it somewhere that had one. It reads the
committed files or it renders an empty state.

WHAT THE SESSIONS SHOW, AND WHERE THAT STOPS. Both sessions produced zero
fills. That establishes the part of the system that ran: each session completed,
consumed captured market data, generated simulated orders, and recorded the risk
layer's refusals. It establishes nothing about fill handling, fee accounting,
inventory behaviour, settlement or P&L, because with no fill none of those paths
executed. The bundle demonstrates that against itself: every one of those
figures is null in its own performance section. The page says so above the first
number, because a reader who skims a table of zeros will otherwise supply their
own interpretation.
"""

import json
from pathlib import Path

import streamlit as st

from components.case_study import load_bundle
from components.styles import configure_page, eyebrow, inject_styles, section_title

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "case_study"

configure_page()
inject_styles()

eyebrow("07", "paper desk case study")

st.markdown("<h2>Paper Desk Case Study</h2>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#888;font-size:14px;'>"
    "Two completed paper market-making sessions, quoted against captured "
    "exchange order books. Simulated orders only &middot; no venue, no money, "
    "no position. An engineering case study, not a performance record.</p>",
    unsafe_allow_html=True,
)


# A short TTL because the empty state tells the reader to add the bundle, and a
# cache keyed only on the path would keep serving the empty state until the
# server restarted.
@st.cache_data(show_spinner=False, ttl=60)
def _load(directory: str):
    path = Path(directory)
    if not (path / "index.json").exists():
        return None
    return load_bundle(path)


bundle = _load(str(BUNDLE))

if bundle is None or not bundle.sessions:
    st.warning("No case-study bundle on this checkout.")
    st.markdown(
        "The page reads sanitized JSON from `dashboard/case_study/`. "
        "That directory is empty or missing here, so there is nothing to "
        "render. No database or credential would help: this page has no other "
        "source."
    )
    st.stop()

# ------------------------------------------------------- the caveat, first
# Before any number. A zero in a table is not a claim; this is.
st.error(
    "**Zero fills. No profitability inference is permitted from this page.**  \n"
    "No order reached a venue. Every order shown was simulated against captured "
    "order books, no money changed hands, and no position was ever held.  \n\n"
    "What the sessions establish is bounded: each one ran to completion, "
    "consumed captured market data, generated simulated orders, and recorded "
    "the risk layer's refusals. They do **not** establish that fill handling, "
    "fee accounting, inventory behaviour, settlement or P&L are correct, "
    "because with no fill none of those paths ever ran — every one of those "
    "figures is null in the data below. Nothing here is a return, an edge, a "
    "break-even result or a validated strategy."
)

st.caption(
    f"Bundle built {bundle.built_at} &middot; schema {bundle.schema} &middot; "
    "read from committed files; no database, no network, no credentials."
)

# --------------------------------------------------------------- the totals
totals = {
    "orders": sum(s.n_orders for s in bundle.sessions),
    "fills": sum(s.n_fills for s in bundle.sessions),
    "incidents": sum(s.n_incidents for s in bundle.sessions),
}
per_session = " + ".join(f"{s.n_orders:,}" for s in bundle.sessions)
per_incident = " + ".join(f"{s.n_incidents:,}" for s in bundle.sessions)

# auto-fit rather than a fixed column count, so the row reflows to one column
# on a phone instead of crushing four cards into 380px.
_cards = [
    ("simulated orders", f"{totals['orders']:,}",
     f"{per_session} across {len(bundle.sessions)} sessions"),
    ("fills", f"{totals['fills']:,}",
     "none; no order reached a venue"),
    ("risk refusals", f"{totals['incidents']:,}",
     f"{per_incident} &middot; exact counts"),
    ("sessions", f"{len(bundle.sessions)}",
     "both completed"),
]
st.markdown(
    "<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));"
    "gap:12px;align-items:stretch;'>"
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

st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

# ------------------------------------------------------------- the sessions
section_title("Sessions")
st.dataframe(
    [{"event": s.event_stem,
      "simulated orders": s.n_orders,
      "fills": s.n_fills,
      "risk refusals": s.n_incidents,
      "started": s.started_at,
      "ended": s.ended_at}
     for s in bundle.sessions],
    hide_index=True, width="stretch")

names = [f"{s.event_stem} — {s.n_orders:,} orders" for s in bundle.sessions]
chosen = st.selectbox("Session", range(len(names)),
                      format_func=lambda i: names[i])
session = bundle.sessions[chosen]

# ------------------------------------------------------- why nothing filled
summary = session.sections.get("incident_summary") or []
if summary:
    section_title("Why nothing filled")
    st.markdown(
        "<p style='color:#888;font-size:14px;'>"
        "Every row is the risk layer refusing to send size. That is the finding "
        "of both sessions: the desk was capped out of its own market before a "
        "counterparty had the chance to trade with it. These counts are exact "
        "totals, not a sample.</p>",
        unsafe_allow_html=True,
    )
    st.dataframe(
        [{"reason": g.get("reason", ""),
          "count": g.get("count", 0),
          "distinct details": g.get("distinct_details", 0),
          "example": g.get("example", "")}
         for g in summary],
        hide_index=True, width="stretch")

# ------------------------------------------------------------ the raw rows
rows = session.sections.get("incidents") or []
if rows:
    shipped = len(rows)
    if session.incidents_are_a_sample:
        label = (f"Sample of {shipped:,} rows out of {session.n_incidents:,} "
                 f"recorded. The totals above are exact; these rows are not all "
                 f"of them.")
    else:
        label = f"All {shipped:,} recorded rows."
    section_title("Refusal rows")
    st.caption(label)
    st.dataframe(rows, hide_index=True, width="stretch")

orders = session.sections.get("orders") or []
if orders:
    section_title("Simulated orders")
    st.caption(
        f"All {len(orders):,} orders this session generated. None was "
        "submitted to any venue."
    )
    st.dataframe(orders, hide_index=True, width="stretch")

# --------------------------------------------------------- what was measured
performance = session.sections.get("performance") or []
if performance:
    section_title("What the session could and could not measure")
    row = performance[0] if isinstance(performance, list) else performance
    measured, unmeasured = [], []
    for key, value in sorted(row.items()):
        if key in ("limitations", "config_versions", "sample_sizes"):
            continue
        (unmeasured if value is None else measured).append((key, value))
    left, right = st.columns(2)
    with left:
        st.markdown("**Measured**")
        st.dataframe([{"metric": k, "value": v} for k, v in measured],
                     hide_index=True, width="stretch")
    with right:
        st.markdown("**Not measured — needed a fill**")
        st.dataframe([{"metric": k, "value": "null"} for k, _ in unmeasured],
                     hide_index=True, width="stretch")

# ------------------------------------------------------------- limitations
if session.limitations:
    section_title("Limitations, as recorded by the session itself")
    for line in session.limitations:
        st.markdown(f"- {line}")

if session.note:
    st.caption(session.note)

with st.expander("how this page gets its data"):
    st.markdown(
        "Three JSON files under `dashboard/case_study/`, committed to this "
        "repository. They are produced by a private export step that reads "
        "retained session databases read-only, applies a per-section allowlist, "
        "sweeps values for credentials, wallet identifiers, webhooks, database "
        "URLs, host addresses and absolute paths, and writes only what survives. "
        "This page imports nothing from that system; it reads the files.\n\n"
        f"Index: `{json.dumps(sorted(p.name for p in BUNDLE.glob('*.json')))}`"
    )
