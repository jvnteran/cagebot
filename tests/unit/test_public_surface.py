"""Guard: nothing in this repository may describe how the engine works.

This repo publishes the analytics layer only. The prediction engine, the
selection rules and the production automation are private. These tests fail
the build if that boundary is crossed by any tracked file — not just the file
someone remembered to check.

A note on how the rules are written. A guard that lists the secrets it is
protecting *is* the disclosure: anyone can read the ban list. So the rules
here are of two kinds, and neither one names a private value:

  * Shape rules match the *form* of a disclosure — a version token, a count
    next to the word "features", an IP address — without naming the value.
  * Family rules list many candidates at once. Banning a dozen ML libraries
    reveals which none of them is in use.

The private taxonomy (strategy labels, trigger names, internal module paths)
cannot be generalised this way, so it is not stored here at all. It is read
from a wordlist kept outside the repository — `CAGEBOT_GUARD_VOCAB`, or
`tests/.private_vocabulary`, which is gitignored. When that list is absent the
vocabulary test skips loudly; every other rule still runs.
"""
import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()

TEXT_SUFFIXES = {".py", ".md", ".sql", ".yml", ".yaml", ".toml", ".txt",
                 ".json", ".cfg", ".ini", ".example", ".sh"}

# Family rule: naming many reveals none.
MODEL_FAMILY_TERMS = [
    "xgboost", "lightgbm", "catboost", "scikit-learn", "sklearn",
    "tensorflow", "pytorch", "keras", "statsmodels",
    "gradient boost", "gradient-boost", "random forest", "neural network",
    "logistic regression", "elastic net",
]

# Lines that pin a dependency or tool version. A version token there is
# ordinary packaging metadata, not a disclosure about the model.
DEPENDENCY_PIN = re.compile(
    r"\b(?:rev|uses|version|python-version|image|ref)\s*[:=]"
    r"|[=><~!]=\s*v?\d"
    r"|@v?\d",
    re.I,
)

# Shape rules: match the form of a disclosure, never the value.
# `skip` marks lines where a match is expected and harmless.
SHAPE_RULES = [
    (re.compile(r"\bv\s*\d+\.\d+\b", re.I), "model version token", DEPENDENCY_PIN),
    (re.compile(r"\b\d{2,4}\s+features?\b", re.I), "feature-space size", None),
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"), "IP address", DEPENDENCY_PIN),
    (re.compile(r"/api/webhooks", re.I), "webhook endpoint", None),
    (re.compile(r"\b[A-Z][A-Z0-9_]{4,}_(?:KEY|TOKEN|SECRET|WEBHOOK)\b"),
     "credential env var", None),
]

# Relations the dashboard may read. Anything else in a FROM/JOIN clause is
# either a private base table or an unreviewed addition.
ALLOWED_RELATIONS = {
    "v_event_accuracy", "v_fight_detail", "v_fighter_current",
    "v_accuracy_by_location", "v_market_audit", "v_strategy_record_public",
    "v_markets_ev_public", "v_markets_funnel_public",
    "fights", "fighters", "events", "odds_snapshots", "overrides",
    "fighter_elo_history",
}

# Per-fight staking columns. On the strategy record, a per-row price beside a
# result reconstructs the selection rule from the outcomes.
STAKING_COLUMNS = ["bet_side", "closing_odds", "clv_pp"]

ENGINE_DIRS = ("pipelines", "scripts", "artifacts", "models", "features",
               "agents", "feature_engineering")


def _tracked_text_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    files = []
    for name in out.split("\0"):
        if not name:
            continue
        path = ROOT / name
        if path.suffix in TEXT_SUFFIXES and path.resolve() != SELF and path.exists():
            files.append(path)
    return files


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _private_vocabulary() -> list[str]:
    """Load the out-of-repo wordlist, or return [] when it is unavailable."""
    raw = os.environ.get("CAGEBOT_GUARD_VOCAB", "")
    if not raw:
        local = ROOT / "tests" / ".private_vocabulary"
        if local.exists():
            raw = _read(local)
    terms = []
    for line in raw.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append(line)
    return terms


def test_repo_has_tracked_files():
    assert _tracked_text_files(), "guard would pass vacuously"


def test_no_model_family_disclosure():
    hits = []
    for path in _tracked_text_files():
        low = _read(path).lower()
        hits += [f"{_rel(path)}: {term}"
                 for term in MODEL_FAMILY_TERMS if term in low]
    assert not hits, "model family disclosed: " + "; ".join(hits)


def test_no_shaped_disclosures():
    hits = []
    for path in _tracked_text_files():
        for lineno, line in enumerate(_read(path).splitlines(), 1):
            for pattern, label, skip in SHAPE_RULES:
                if skip is not None and skip.search(line):
                    continue
                match = pattern.search(line)
                if match:
                    hits.append(
                        f"{_rel(path)}:{lineno}: {label} ({match.group(0)!r})")
    assert not hits, "shaped disclosure: " + "; ".join(hits)


def test_no_private_vocabulary():
    vocab = _private_vocabulary()
    if not vocab:
        pytest.skip(
            "private vocabulary wordlist unavailable — set CAGEBOT_GUARD_VOCAB "
            "or add tests/.private_vocabulary to run this check"
        )
    hits = []
    for path in _tracked_text_files():
        low = _read(path).lower()
        hits += [f"{_rel(path)}: <redacted term>"
                 for term in vocab if term.lower() in low]
    assert not hits, "private vocabulary in published files: " + "; ".join(hits)


def test_dashboard_reads_only_allowed_relations():
    illegal = {}
    for path in (ROOT / "dashboard").rglob("*.py"):
        text = _read(path)
        found = set(re.findall(r"\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)", text))
        found |= set(re.findall(r"\bJOIN\s+([A-Za-z_][A-Za-z0-9_]*)", text))
        extra = found - ALLOWED_RELATIONS
        if extra:
            illegal[_rel(path)] = sorted(extra)
    assert not illegal, f"dashboard queries unreviewed relations: {illegal}"


def test_market_page_summarises_the_record_but_never_itemises_it():
    """Opening/closing prices are fine on the market-audit query — that is
    model output priced against a public line. They are not fine on the
    strategy record, where a per-row price beside a result reveals the rule.
    """
    page = next((ROOT / "dashboard" / "pages").glob("*Market_Performance.py"), None)
    assert page is not None, "Market Performance page not found"
    text = _read(page)

    record_sql = re.search(r'SQL_RECORD\s*=\s*"""(.*?)"""', text, flags=re.S)
    assert record_sql, "SQL_RECORD query not found"
    hits = [c for c in STAKING_COLUMNS if c in record_sql.group(1)]
    assert not hits, f"strategy record itemised by: {hits}"

    all_sql = "\n".join(re.findall(r'"""(.*?)"""', text, flags=re.S))
    assert not re.search(r"\bFROM\s+v_betting_public\b", all_sql), \
        "page reads the per-bet blotter view"

    # The trigger table is a permitted aggregate; a table over `rec` is not.
    assert not re.search(r"st\.dataframe\(\s*rec", text), \
        "the strategy record renders as a table"
    assert "rec_display" not in text, "per-bet log frame reintroduced"


def test_no_engine_directories():
    present = [d for d in ENGINE_DIRS if (ROOT / d).exists()]
    assert not present, f"engine-side directories in public repo: {present}"


def test_no_credentials_committed():
    pattern = re.compile(
        r"postgres(?:ql)?://[^\s\"']*:[^\s\"'@]*@(?!localhost|host/)"
        r"|(?:api[_-]?key|secret|token)\s*[:=]\s*[\"'][A-Za-z0-9_\-]{16,}",
        re.I,
    )
    hits = [_rel(p) for p in _tracked_text_files() if pattern.search(_read(p))]
    assert not hits, f"possible credential committed in: {hits}"
