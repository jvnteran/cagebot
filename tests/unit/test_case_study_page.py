"""Drive the case-study page the way a visitor's browser does.

The claim is cold start, and it is tested by removing the things a fallback
would reach for rather than by asserting that no fallback was written:

  * EVERY environment variable is deleted, bar the handful an interpreter needs
    to exist at all. Deleting them by sweep rather than by name matters — a
    named list only covers the credentials somebody remembered, and this
    repository is public precisely because nobody should have to remember.
  * `sqlite3.connect` raises. A page that opened a local database would fail
    here instead of quietly working on the one machine that has one.
  * `socket.socket` raises. Same argument for anything that would fetch.

Driving the screen is not redundant with the unit tests. A page can read the
right numbers and still print a wider claim than the numbers support, because
the prose is written by hand and the numbers are not.
"""
import socket
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PAGE = next((ROOT / "dashboard" / "pages").glob("*Desk_Case_Study.py"), None)

#: Without these an interpreter cannot reliably start a subprocess or find a
#: home directory. Neither is a credential, and neither is a data source.
KEEP = ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "PYTEST_CURRENT_TEST")

EXPECTED = {
    "UFC_2026_08_29": {"orders": 55, "fills": 0, "incidents": 6233},
    "UFC_2026_09_05": {"orders": 166, "fills": 0, "incidents": 13160},
}

NEGATIONS = ("not ", "no ", "never", "nothing", "cannot", "n't ", "without")
UNSUPPORTABLE = ("profitable", "break-even", "validated strategy",
                 "validated edge", "end to end", "end-to-end",
                 "settlement correctness")


@pytest.fixture
def cold(monkeypatch):
    """No environment, no database, no network."""
    import os
    for name in list(os.environ):
        if name not in KEEP:
            monkeypatch.delenv(name, raising=False)

    def no_database(*args, **kwargs):
        raise AssertionError("the case-study page opened a database")

    def no_network(*args, **kwargs):
        raise AssertionError("the case-study page opened a socket")

    monkeypatch.setattr(sqlite3, "connect", no_database)
    monkeypatch.setattr(socket, "socket", no_network)
    return True


def _run():
    from streamlit.testing.v1 import AppTest

    for extra in (str(ROOT), str(ROOT / "dashboard")):
        if extra not in sys.path:
            sys.path.insert(0, extra)
    app = AppTest.from_file(str(PAGE), default_timeout=300)
    app.run()
    return app


def _rendered(app) -> str:
    parts = []
    for block in (app.error, app.warning, app.markdown, app.caption,
                  app.info, app.success):
        parts += [str(element.value) for element in block]
    return " ".join(parts)


def test_the_page_exists_and_follows_the_page_naming_convention():
    assert PAGE is not None, "no Desk_Case_Study page under dashboard/pages"
    assert PAGE.name[0].isdigit(), f"{PAGE.name} has no ordinal prefix"


def test_the_page_renders_with_no_environment_no_database_and_no_network(cold):
    app = _run()
    assert not app.exception, \
        f"the page raised: {[e.value for e in app.exception]}"


def test_the_page_shows_both_sessions_with_their_exact_counts(cold):
    app = _run()
    assert not app.exception, [e.value for e in app.exception]

    frames = [f.value for f in app.dataframe]
    assert frames, "the page rendered no table"
    rows = [row for frame in frames
            for row in (frame.to_dict("records")
                        if hasattr(frame, "to_dict") else frame)]

    for stem, counts in EXPECTED.items():
        match = [r for r in rows if r.get("event") == stem]
        assert match, f"{stem} is not on the page"
        row = match[0]
        assert row["simulated orders"] == counts["orders"]
        assert row["fills"] == counts["fills"]
        assert row["risk refusals"] == counts["incidents"]


def test_the_page_shows_the_combined_totals(cold):
    """55 + 166 orders and 6,233 + 13,160 refusals, summed and itemised."""
    app = _run()
    rendered = _rendered(app)
    assert "221" in rendered, "the combined order count is not shown"
    assert "19,393" in rendered, "the combined refusal count is not shown"
    assert "55" in rendered and "166" in rendered, \
        "the per-session order counts are not shown"
    assert "6,233" in rendered and "13,160" in rendered, \
        "the per-session refusal counts are not shown"


def test_the_page_says_no_order_reached_a_venue_before_any_number(cold):
    app = _run()
    errors = " ".join(str(e.value) for e in app.error).lower()
    assert errors, "the boundary is not rendered as a notice at all"
    assert "no order reached a venue" in errors
    assert "no profitability inference is permitted" in errors


def test_the_page_labels_the_incident_rows_as_a_sample(cold):
    app = _run()
    captions = " ".join(str(c.value) for c in app.caption).lower()
    assert "sample" in captions, \
        "the refusal rows are shown without saying they are a sample"
    assert "6,233" in captions or "13,160" in captions, \
        "the sample caption does not carry the exact recorded total"


@pytest.mark.parametrize("banned", UNSUPPORTABLE)
def test_the_rendered_prose_asserts_no_claim_the_evidence_cannot_carry(cold,
                                                                       banned):
    rendered = _rendered(_run()).lower()
    assert rendered.strip(), "nothing rendered; this would pass vacuously"
    for sentence in rendered.replace(chr(0x2014), ". ").split("."):
        if banned not in sentence:
            continue
        assert any(n in sentence for n in NEGATIONS), \
            f"the page asserts {banned!r}: {sentence.strip()[:140]}"


def test_the_page_describes_itself_as_a_paper_session_case_study(cold):
    rendered = _rendered(_run()).lower() + " " + PAGE.read_text().lower()
    assert "paper" in rendered
    assert "case study" in rendered
    assert "simulated" in rendered


# --- the harness itself -------------------------------------------------------

def test_the_cold_fixture_really_removes_the_database_and_the_network(cold):
    """Guard the guard. A fixture that patched the wrong name would let every
    test above pass while proving nothing."""
    with pytest.raises(AssertionError, match="opened a database"):
        sqlite3.connect(":memory:")
    with pytest.raises(AssertionError, match="opened a socket"):
        socket.socket()


def test_a_page_that_opened_a_database_would_be_caught(cold, tmp_path):
    """The failure this suite exists to prevent, reproduced.

    Without this, `test_the_page_renders_...` is satisfied by any page that
    never had a fallback in the first place, and would stay green if one were
    added and the patch stopped working.
    """
    from streamlit.testing.v1 import AppTest

    stand_in = tmp_path / "leaky_page.py"
    stand_in.write_text(
        "import sqlite3\n"
        "import streamlit as st\n"
        "st.write('falling back')\n"
        "sqlite3.connect(':memory:')\n"
    )
    app = AppTest.from_file(str(stand_in), default_timeout=300)
    app.run()
    assert app.exception, "a page that opened a database was not caught"
    assert "opened a database" in " ".join(str(e.value) for e in app.exception)
