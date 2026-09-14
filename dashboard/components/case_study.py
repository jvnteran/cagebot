"""Read the committed case-study bundle. Files in, dataclasses out.

Deliberately the dullest module in the repository. It opens no database, makes
no request, reads no environment variable and imports nothing beyond the
standard library, because the page it feeds has to render from a fresh clone
with no credentials of any kind. Anything cleverer than `json.load` would be a
way for that to stop being true.

Three rules about what it will read, and all three are refusals rather than
fixes:

  * A bundle entry names a file by PLAIN FILENAME, checked twice - once on the
    name and once on where it actually resolves to. The index is data, and data
    that can name `../../.env` is a file-read primitive pointed at whoever is
    hosting the page.
  * A section the page does not know how to render is DROPPED. A bundle built
    by a newer exporter may carry sections this page has never seen; rendering
    them blind is how something private reaches a public surface without
    anybody deciding that it should.
  * A bundle this reader does not understand, or cannot read, raises
    `BundleUnreadable` rather than whatever the filesystem or the JSON parser
    happened to raise. The page turns that into an empty state. An uncaught
    `FileNotFoundError` on a public page prints the server's absolute path and
    the page source into the browser.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

#: Bumped when the shape changes in a way this reader cannot absorb. Enforced
#: in `load_bundle`: a constant nothing compares against is a comment.
BUNDLE_SCHEMA = 1

#: Sections this reader will carry. Narrower than what the page draws - the
#: page renders `incident_summary`, `incidents`, `orders` and `performance`,
#: and the rest are carried for a caller that wants them. The point of the set
#: is that anything NOT named here never reaches a caller at all.
READABLE_SECTIONS = frozenset({
    "session", "orders", "fills", "incidents", "incident_summary",
    "mappings", "performance",
})


class BundleUnreadable(ValueError):
    """This bundle will not be rendered, and here is the reason.

    A `ValueError` subclass on purpose: a caller that only wants "bad input"
    keeps working, and the page can still catch precisely this.
    """


@dataclass(frozen=True)
class Session:
    """One paper session, exactly as the bundle recorded it."""

    session_id: str
    event_stem: str
    started_at: str = ""
    ended_at: str = ""
    n_orders: int = 0
    n_fills: int = 0
    n_incidents: int = 0
    note: str = ""
    limitations: tuple = ()
    sections: dict = field(default_factory=dict)
    #: True when `sections["incidents"]` holds fewer rows than `n_incidents`.
    #: Carried on the row itself so no table can show 200 of 6,233 without the
    #: caller having been told.
    incidents_are_a_sample: bool = False


@dataclass(frozen=True)
class Bundle:
    built_at: str
    schema: int
    sessions: tuple


def _within(directory, name) -> Path:
    """`directory / name`, or a refusal. Two independent checks.

    The NAME check asks "is this a filename", which a traversal cannot be. It
    is the stronger question, but it is blind to one thing: a plain filename
    that is a SYMLINK out of the directory passes it and reads the target. So
    the resolved location is checked as well. Either alone leaves a hole -
    `Path("..").name` is `".."`, which the name check would otherwise accept.
    """
    if not isinstance(name, str) or not name:
        raise BundleUnreadable(f"bundle entry is not a filename: {name!r}")
    candidate = Path(name)
    if candidate.name != name or candidate.is_absolute() or name in (".", ".."):
        raise BundleUnreadable(f"bundle entry is not a plain filename: {name!r}")

    directory = Path(directory)
    target = directory / candidate.name
    try:
        root, resolved = directory.resolve(), target.resolve()
    except OSError as exc:                      # a broken or looping symlink
        raise BundleUnreadable(f"bundle entry cannot be resolved: {name!r}") from exc
    if resolved.parent != root:
        raise BundleUnreadable(
            f"bundle entry resolves outside the bundle: {name!r}")
    return target


def _readable(payload: dict) -> dict:
    """Only the sections this reader was taught about."""
    return {key: value for key, value in payload.items()
            if key in READABLE_SECTIONS}


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        # The filename, never the path: the page renders this and the page is
        # public. `/mount/src/...` is not a secret, but it is not a visitor's
        # business either.
        raise BundleUnreadable(f"{path.name} could not be read") from exc
    if not isinstance(payload, dict):
        raise BundleUnreadable(f"{path.name} is not an object")
    return payload


def load_bundle(directory) -> Bundle | None:
    """The bundle at `directory`, or None when there is nothing to show.

    None means "no bundle here", which is a normal state for a checkout that
    has not got one. `BundleUnreadable` means "there is one and it is wrong",
    which is not the same thing and must not be silently equated with it.
    """
    directory = Path(directory)
    index_path = directory / "index.json"
    if not index_path.exists():
        return None

    index = _load_json(index_path)
    schema = index.get("schema")
    if schema != BUNDLE_SCHEMA:
        raise BundleUnreadable(
            f"bundle schema {schema!r}; this page reads {BUNDLE_SCHEMA}")

    entries = index.get("sessions")
    if not isinstance(entries, list):
        raise BundleUnreadable("bundle index carries no session list")

    sessions = []
    for entry in entries:
        if not isinstance(entry, dict) or "file" not in entry:
            raise BundleUnreadable("bundle index entry names no file")
        payload = _load_json(_within(directory, entry["file"]))
        counts = payload.get("counts")
        counts = counts if isinstance(counts, dict) else {}
        try:
            orders = int(counts.get("orders", 0))
            fills = int(counts.get("fills", 0))
            incidents = int(counts.get("incidents", 0))
        except (TypeError, ValueError) as exc:
            raise BundleUnreadable("bundle counts are not numbers") from exc
        sessions.append(Session(
            session_id=str(payload.get("session_id",
                                       entry.get("session_id", ""))),
            event_stem=str(payload.get("event_stem",
                                       entry.get("event_stem", ""))),
            started_at=str(payload.get("started_at", "")),
            ended_at=str(payload.get("ended_at", "")),
            # The bundle's own totals, never recomputed from the rows that
            # shipped: the incident rows are a sample, so a recomputed total
            # would silently be the sample size wearing the total's label.
            n_orders=orders,
            n_fills=fills,
            n_incidents=incidents,
            note=str(payload.get("note", "")),
            limitations=tuple(payload.get("limitations", ())),
            sections=_readable(payload),
            incidents_are_a_sample=bool(payload.get("incidents_are_a_sample")),
        ))
    return Bundle(built_at=str(index.get("built_at", "")),
                  schema=BUNDLE_SCHEMA,
                  sessions=tuple(sessions))
