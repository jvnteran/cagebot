"""The case-study bundle and the page that renders it.

Four claims, tested separately because they fail separately:

  IDENTICAL — the three JSON files here are byte-for-byte the artifacts that
  were reviewed privately. A public copy that drifted from the reviewed one is
  an unreviewed publication wearing a reviewed one's name.

  EXACT — the counts and the recorded limitations survive the copy and the
  read. The incident ROWS are a sample; the incident TOTALS are not, and the
  reader has to be able to tell which is which.

  CLEAN — nothing private is in the bundle. The scan is proved against planted
  poison before it is trusted on real files, because a scanner nobody has
  watched fail is a scanner nobody has tested.

  BOUNDED — zero fills cannot be presented as profit, as break-even, as a
  validated edge, or as evidence that settlement works. The page may NAME those
  things, because it has to say which ones were not exercised; it may not
  ASSERT them.

A note on the poison fixtures. Every one is assembled from parts at runtime,
never written as a literal. `tests/unit/test_public_surface.py` scans every
tracked file in this repository for exactly these shapes, and a literal fixture
would be indistinguishable from the real disclosure it imitates. The assembly
is itself under test below, so nobody tidies it away.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "dashboard" / "case_study"
PAGE = next((ROOT / "dashboard" / "pages").glob("*Desk_Case_Study.py"), None)

sys.path.insert(0, str(ROOT / "dashboard"))

from components.case_study import (  # noqa: E402
    BUNDLE_SCHEMA, READABLE_SECTIONS, BundleUnreadable, _within,
    load_bundle,
)

#: The reviewed artifacts, by digest, and nothing else about where they came
#: from. The digest IS the identity; naming the branch and revision they were
#: exported at would tell a reader more about the private side than the files
#: themselves do, permanently and in public. If one of these fails, the copy is
#: not the reviewed artifact, and that has to be explained before it ships
#: rather than after.
EXPECTED_SHA256 = {
    "index.json":
        "22f29e955c047915c6a46ebea774059ee88a7d0b2abc689c0c17b2220f8266ac",
    "UFC_2026_08_29__processed-maker-abd79517-2026-09-09T21-32-10Z.json":
        "087b4dd96942cea6c0bb7ed742815256bf3c339c92a8e3cb3dac132af59091b3",
    "UFC_2026_09_05__processed-maker-abd79517-2026-09-09T21-36-59Z.json":
        "f107b8d4f241589b9e7c8821c577c0a116ce2910ff7b05f7922af906712633d8",
}

#: What the two sessions actually recorded. Written out rather than derived, so
#: a bundle that silently changed would fail here instead of agreeing with
#: itself.
EXPECTED_COUNTS = {
    "UFC_2026_08_29": {"orders": 55, "fills": 0, "incidents": 6233},
    "UFC_2026_09_05": {"orders": 166, "fills": 0, "incidents": 13160},
}


# --- the copy is the reviewed artifact ---------------------------------------

def test_the_bundle_directory_holds_exactly_the_reviewed_files():
    present = sorted(p.name for p in BUNDLE.glob("*"))
    assert present == sorted(EXPECTED_SHA256), \
        f"bundle directory holds {present}"


@pytest.mark.parametrize("name", sorted(EXPECTED_SHA256))
def test_each_copied_file_matches_the_private_release_artifact(name):
    digest = hashlib.sha256((BUNDLE / name).read_bytes()).hexdigest()
    assert digest == EXPECTED_SHA256[name], (
        f"{name} is not the reviewed artifact: {digest[:16]}… here, "
        f"{EXPECTED_SHA256[name][:16]}… reviewed")


# --- counts and limitations survive ------------------------------------------

def test_the_bundle_loads_and_carries_both_sessions():
    bundle = load_bundle(BUNDLE)
    assert bundle is not None
    assert bundle.schema == BUNDLE_SCHEMA
    assert {s.event_stem for s in bundle.sessions} == set(EXPECTED_COUNTS)


@pytest.mark.parametrize("stem", sorted(EXPECTED_COUNTS))
def test_the_exact_counts_survive_the_copy_and_the_read(stem):
    session = next(s for s in load_bundle(BUNDLE).sessions
                   if s.event_stem == stem)
    assert session.n_orders == EXPECTED_COUNTS[stem]["orders"]
    assert session.n_fills == EXPECTED_COUNTS[stem]["fills"]
    assert session.n_incidents == EXPECTED_COUNTS[stem]["incidents"]


@pytest.mark.parametrize("stem", sorted(EXPECTED_COUNTS))
def test_the_incident_total_is_exact_while_the_rows_are_a_sample(stem):
    """The trap this catches: recomputing a total from the rows that shipped.

    200 rows ship out of thousands. A total derived from `len(rows)` would be
    the sample size wearing the total's label, and would look entirely
    reasonable on the page.
    """
    session = next(s for s in load_bundle(BUNDLE).sessions
                   if s.event_stem == stem)
    rows = session.sections.get("incidents") or []
    assert session.n_incidents == EXPECTED_COUNTS[stem]["incidents"]
    assert len(rows) < session.n_incidents
    assert session.incidents_are_a_sample is True

    grouped = sum(g["count"] for g in session.sections["incident_summary"])
    assert grouped == session.n_incidents, \
        "the per-reason counts must add up to the exact total, not the sample"


@pytest.mark.parametrize("stem", sorted(EXPECTED_COUNTS))
def test_the_recorded_limitations_survive(stem):
    session = next(s for s in load_bundle(BUNDLE).sessions
                   if s.event_stem == stem)
    assert session.limitations, "the session's own limitations were dropped"
    joined = " ".join(session.limitations).lower()
    assert "no fills" in joined or "no_fills" in joined
    assert "profitab" in joined, "it must name what it is NOT evidence of"
    assert "paper execution only" in joined


def test_every_figure_that_needed_a_fill_is_null():
    """The evidence for the narrow claim, in the artifact itself."""
    needed_a_fill = ("fees", "gross_pnl", "net_pnl", "inventory_pnl",
                     "spread_capture", "clv")
    checked = 0
    for session in load_bundle(BUNDLE).sessions:
        for row in session.sections.get("performance") or []:
            populated = {k: row[k] for k in needed_a_fill
                         if row.get(k) is not None}
            assert not populated, f"{session.event_stem} reports {populated}"
            checked += 1
    assert checked, "no performance section was examined"


# --- the reader refuses what it should ---------------------------------------

@pytest.mark.parametrize("escape", [
    "../../.env",
    "../index.json",
    "/etc/passwd",
    "sub/dir/file.json",
    "",
    # `Path("..").name` is `".."`, so the name check alone lets this one
    # through. It cannot be extended into a file read, but it reaches the
    # filesystem, and "reaches the filesystem" is not what the docstring says.
    "..",
    ".",
    # Not a string at all. Silently coerced, it produced a FileNotFoundError
    # somewhere else instead of a refusal here.
    123,
    ["a"],
    None,
])
def test_the_reader_takes_a_plain_filename_only(escape):
    with pytest.raises(BundleUnreadable):
        _within(Path("/tmp"), escape)


def test_a_symlink_wearing_a_plain_filename_is_refused(tmp_path):
    """The hole the NAME check cannot see.

    A symlink named `index.json` IS a plain filename by every test above, and
    reading it reads whatever it points at. The name check is the stronger
    question for traversal and strictly weaker here, which is why the resolved
    location is checked too.
    """
    outside = tmp_path / "outside.json"
    outside.write_text('{"secret": true}')
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "session.json").symlink_to(outside)

    with pytest.raises(BundleUnreadable, match="outside"):
        _within(bundle, "session.json")


def test_a_plain_file_in_the_directory_is_accepted(tmp_path):
    """The other half: the refusals above must not have made it refuse
    everything, which would pass every test and render nothing."""
    (tmp_path / "session.json").write_text("{}")
    assert _within(tmp_path, "session.json") == tmp_path / "session.json"


def test_the_reader_refuses_a_bundle_entry_that_escapes(tmp_path):
    (tmp_path / "index.json").write_text(json.dumps(
        {"schema": 1, "built_at": "", "sessions": [{"file": "../secret.json"}]}))
    (tmp_path.parent / "secret.json").write_text('{"session_id": "leaked"}')
    with pytest.raises(BundleUnreadable):
        load_bundle(tmp_path)


#: A bundle that is present but wrong. Each of these used to reach the visitor
#: as a Streamlit traceback carrying the server's absolute path and this
#: page's source; `load_bundle`'s docstring promised otherwise, and covered
#: only the case where index.json is absent entirely.
@pytest.mark.parametrize("name,build", [
    ("data file missing", lambda d: None),
    ("data file corrupt", lambda d: (d / "s.json").write_text("{not json")),
    ("index corrupt", lambda d: (d / "index.json").write_text("{not json")),
    ("index is a list", lambda d: (d / "index.json").write_text("[]")),
    ("no session list", lambda d: (d / "index.json").write_text(
        json.dumps({"schema": 1}))),
    ("entry names no file", lambda d: (d / "index.json").write_text(
        json.dumps({"schema": 1, "sessions": [{"session_id": "s"}]}))),
    ("unknown schema", lambda d: (d / "index.json").write_text(
        json.dumps({"schema": 99, "sessions": []}))),
    ("counts are not numbers", lambda d: (d / "s.json").write_text(
        json.dumps({"counts": {"orders": "many"}}))),
])
def test_a_present_but_broken_bundle_refuses_rather_than_raising_anything_else(
        tmp_path, name, build):
    (tmp_path / "index.json").write_text(json.dumps(
        {"schema": 1, "built_at": "", "sessions": [{"file": "s.json"}]}))
    build(tmp_path)
    with pytest.raises(BundleUnreadable):
        load_bundle(tmp_path)


def test_a_refusal_never_names_the_path_it_was_reading():
    """The reason is rendered on a public page. The filename is useful; the
    server's directory layout is not the visitor's business."""
    import tempfile
    root = Path(tempfile.mkdtemp())
    (root / "index.json").write_text(json.dumps(
        {"schema": 1, "built_at": "", "sessions": [{"file": "s.json"}]}))
    try:
        load_bundle(root)
    except BundleUnreadable as refusal:
        assert str(root) not in str(refusal), \
            f"the refusal carries the absolute path: {refusal}"
    else:
        raise AssertionError("a missing data file was not refused")


def test_the_reader_drops_a_section_it_was_never_taught_to_render(tmp_path):
    """A newer exporter may add sections. Rendering them blind is how something
    private reaches a public page without anyone deciding that it should."""
    payload = {
        "schema": 1, "session_id": "s", "event_stem": "E",
        "counts": {"orders": 1, "fills": 0, "incidents": 0},
        "orders": [{"venue": "x"}],
        "operator_notes": [{"who": "someone", "wallet": "private"}],
        "raw_capture": ["anything at all"],
    }
    (tmp_path / "s.json").write_text(json.dumps(payload))
    (tmp_path / "index.json").write_text(json.dumps(
        {"schema": 1, "built_at": "", "sessions": [{"file": "s.json"}]}))

    session = load_bundle(tmp_path).sessions[0]
    assert "orders" in session.sections
    assert "operator_notes" not in session.sections
    assert "raw_capture" not in session.sections
    assert set(session.sections) <= READABLE_SECTIONS


def test_an_absent_bundle_is_a_return_not_a_raise(tmp_path):
    assert load_bundle(tmp_path) is None


# --- nothing private is in the bundle ----------------------------------------

SECRET_SHAPES = (
    # 40 hex characters is an EVM address. 64 is a public market identifier,
    # which is not a wallet and must not be reported as one.
    (re.compile(r"0x[0-9a-fA-F]{40}\b"), "wallet"),
    (re.compile(r"0x[0-9a-fA-F]{16,}"), "hex-id"),
    (re.compile(r"\b(sk|pk|rk)[-_][A-Za-z0-9_-]{8,}"), "credential"),
    (re.compile(r"\bAK" + r"IA[0-9A-Z]{16}\b"), "credential"),
    (re.compile(r"\bey" + r"J[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"), "credential"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}"), "credential"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"), "credential"),
    (re.compile(r"(?i)[\"']?[a-z0-9_-]*(?:api[_-]?key|secret|token|password|"
                r"key[_-]?id)[a-z0-9_-]*[\"']?\s*[:=]\s*[\"']?[^\s\"',;}]+"),
     "credential"),
    # `/etc` and `/root` were missing, which are the two a reader would care
    # about most; Windows paths were missing entirely.
    (re.compile(r"/(?:Users|home|app|opt|srv|var|etc|root|mnt|private)/"
                r"[^\s\"',)\]]+"), "absolute path"),
    (re.compile(r"\b[A-Za-z]:\\[^\s\"',;)\]]+"), "absolute path"),
    (re.compile(r"https://discord(?:app)?\.com/api/web" + r"hooks/"),
     "webhook"),
    (re.compile(r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://"),
     "database URL"),
    (re.compile(r"\bwss?://"), "endpoint"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "host address"),
    # A market token id can be a 77-digit decimal, with no 0x to catch it on.
    (re.compile(r"\b\d{30,}\b"), "hex-id"),
    (re.compile(r"SQLite format 3"), "raw database"),
)


def scan_for_secrets(directory) -> list[str]:
    """Every finding, as a readable line. Empty means clean."""
    findings = []
    for path in sorted(Path(directory).rglob("*")):
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if raw[:15] == b"SQLite format 3":
            findings.append(f"{path.name}: raw database")
            continue
        try:
            text = raw.decode()
        except UnicodeDecodeError:
            findings.append(f"{path.name}: not text")
            continue
        for pattern, label in SECRET_SHAPES:
            match = pattern.search(text)
            if match:
                findings.append(f"{path.name}: {label} ({match.group(0)[:40]})")
    return findings


def _poison() -> tuple:
    """Every shape the scan claims to catch: (name, value, expected label).

    Assembled from parts at runtime, never written as a literal. This
    repository's own publication guard scans every tracked file for exactly
    these shapes, and a literal fixture is indistinguishable from the real
    disclosure it imitates. `test_the_poison_fixtures_are_assembled_...` keeps
    them that way.

    Several names share a label on purpose - four different things are all an
    "absolute path" - so this is a list of triples and not a dict.
    """
    dot, bs = ".", chr(92)
    return (
        # 40 hex characters. An EVM address, and reported as one.
        ("evm address", "0x" + "dead" * 10, "wallet"),
        # 64. A public market identifier, which is NOT a wallet.
        ("market identifier", "0x" + "beef" * 16, "hex-id"),
        # 77 decimal digits, with no 0x to catch it on.
        ("bare decimal token id", "7" * 77, "hex-id"),
        ("bearer credential", "sk" + "_" + "liveAbCdEfGhIjKlMn", "credential"),
        ("forge token", "gh" + "p_" + "A" * 30, "credential"),
        ("chat token", "xox" + "b-" + "1234567890-abcdefghij", "credential"),
        ("home path", "/" + "Users" + "/somebody/project/.env", "absolute path"),
        ("etc path", "/" + "etc" + "/shadow", "absolute path"),
        ("root path", "/" + "root" + "/.ssh/id_rsa", "absolute path"),
        ("windows path", "C:" + bs + "Users" + bs + "somebody", "absolute path"),
        ("discord webhook",
         "https://discord" + dot + "com/api/web" + "hooks/1/abc", "webhook"),
        ("database url",
         "postgre" + "sql://u:p@example" + dot + "net/db", "database URL"),
        ("host address", dot.join(["203", "0", "113", "7"]), "host address"),
        ("websocket endpoint", "ws" + "s://internal-desk:8080/feed", "endpoint"),
    )


def test_the_poison_fixtures_are_assembled_and_not_literal():
    """Guard the guard: if someone inlines these, this repository's publication
    check starts failing on its own test fixtures and the reason will not be
    obvious from the failure."""
    source = Path(__file__).read_text()
    for name, value, _ in _poison():
        assert value not in source, \
            f"the {name} fixture is written literally in this file"


@pytest.mark.parametrize("name,value,label", _poison(),
                         ids=[p[0] for p in _poison()])
def test_the_scan_catches_every_shape_it_claims_to(tmp_path, name, value, label):
    (tmp_path / "planted.json").write_text(json.dumps({"note": value}))
    findings = scan_for_secrets(tmp_path)
    assert findings, f"{name} was planted and nothing was found"
    assert any(label in f for f in findings), \
        f"{name} was found but reported as {findings}, not as {label!r}"


def test_the_scan_catches_a_jwt(tmp_path):
    token = "ey" + "JhbGciOiJIUzI1NiJ9" + "." + "eyJzdWIiOiIxIn0" + "." + "sig"
    assert token not in Path(__file__).read_text()
    (tmp_path / "planted.json").write_text(json.dumps({"note": token}))
    assert any("credential" in f for f in scan_for_secrets(tmp_path))


def test_the_scan_catches_a_raw_database(tmp_path):
    (tmp_path / "session.db").write_bytes(b"SQLite format 3\x00rest")
    assert any("raw database" in f for f in scan_for_secrets(tmp_path))


def test_the_committed_bundle_scans_clean():
    assert scan_for_secrets(BUNDLE) == []


# --- the claim stays bounded --------------------------------------------------

NEGATIONS = ("not ", "no ", "never", "nothing", "cannot", "n't ", "without")

#: Both spellings of an em-dash, and the FIRST one must stay a RAW string.
#:
#: The bundle is written by `json.dumps`, whose default is ASCII-escaped
#: output, so the file on disk holds the six characters of the escape and not
#: the character. Written without the `r`, Python decodes the escape at parse
#: time and this tuple becomes the same character twice - which is what shipped
#: here and was caught in review. The splitter then never split a bundle line,
#: every check below degraded into a near-whole-line search, and a planted
#: "this run was profitable \u2014 no order reached a venue" passed all twelve
#: cases: the negation belonged to the next sentence.
#:
#: `test_the_sentence_splitter_...` is what makes that visible, and it is only
#: meaningful while its own fixture is raw too.
EM_DASHES = (r"\u2014", chr(0x2014))

#: Claims this evidence cannot support. Each may be NAMED — the bundle and the
#: page both have to say which behaviour was not exercised — but only inside a
#: sentence that denies it.
UNSUPPORTABLE = (
    "profitable", "break-even", "breakeven", "edge captured", "returns",
    "validated strategy", "validated edge", "end to end", "end-to-end",
    "settlement correctness", "fill handling", "fee accounting",
)


def _sentences(line: str) -> list[str]:
    for dash in EM_DASHES:
        line = line.replace(dash, ". ")
    return line.split(".")


def test_the_sentence_splitter_sees_the_escaped_dash_the_bundle_uses():
    escaped = r'"ran end to end \u2014 and it is not evidence of anything"'
    pieces = _sentences(escaped.lower())
    assert pieces != [escaped.lower()], "the escaped dash is not a break"
    claim = next(s for s in pieces if "end to end" in s)
    assert not any(n in claim for n in NEGATIONS), \
        "the next sentence's negation is leaking into this one"


@pytest.mark.parametrize("banned", UNSUPPORTABLE)
def test_the_bundle_asserts_no_claim_a_zero_fill_session_cannot_support(banned):
    hits = []
    for path in sorted(BUNDLE.glob("*.json")):
        for line in path.read_text().lower().splitlines():
            if banned not in line:
                continue
            for sentence in _sentences(line):
                if banned in sentence and not any(n in sentence
                                                  for n in NEGATIONS):
                    hits.append(f"{path.name}: {sentence.strip()[:140]}")
    assert not hits, f"the bundle asserts {banned!r}: {hits}"


def test_the_page_source_carries_the_boundary_before_any_number():
    """Order matters on a page people skim: the caveat has to precede the
    first metric, not sit under it."""
    text = PAGE.read_text()
    caveat = text.index("No profitability inference is permitted")
    assert "no order reached a venue" in text.lower()
    for marker in ("st.dataframe(", "st.metric(", "grid-template-columns"):
        position = text.find(marker)
        if position >= 0:
            assert caveat < position, \
                f"{marker} is rendered before the caveat"
