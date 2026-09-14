"""Read the committed case-study bundle. Files in, dataclasses out.

Deliberately the dullest module in the repository. It opens no database, makes
no request, reads no environment variable and imports nothing beyond the
standard library, because the page it feeds has to render from a fresh clone
with no credentials of any kind. Anything cleverer than `json.load` would be a
way for that to stop being true.

Two rules about what it will read, and both are refusals rather than fixes:

  * A bundle entry names a file by PLAIN FILENAME. Not a path, not a parent
    reference, not an absolute path. The index is data, and data that can name
    `../../.env` is a file-read primitive pointed at whoever is hosting the
    page.
  * A section the page does not know how to render is DROPPED, not passed
    through. A bundle built by a newer exporter may carry sections this page
    has never seen; rendering them blind is how something private reaches a
    public surface without anybody deciding that it should.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

#: Bumped when the shape changes in a way this reader cannot absorb.
BUNDLE_SCHEMA = 1

#: The only sections this page renders. Everything else in a bundle file is
#: ignored — see the module docstring for why that is a refusal and not a bug.
READABLE_SECTIONS = frozenset({
    "session", "orders", "fills", "incidents", "incident_summary",
    "mappings", "performance",
})


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


def _within(directory: Path, name: str) -> Path:
    """`directory / name`, or a refusal.

    `Path.resolve()` comparison is the usual approach and it is the weaker one:
    it answers "did this escape", which means the traversal has already been
    constructed and is being audited. This answers "is this a filename", which
    a traversal cannot be.
    """
    candidate = Path(str(name))
    if candidate.name != str(name) or candidate.is_absolute() or not name:
        raise ValueError(f"bundle entry is not a plain filename: {name!r}")
    return Path(directory) / candidate.name


def _readable(payload: dict) -> dict:
    """Only the sections this page knows how to render."""
    return {key: value for key, value in payload.items()
            if key in READABLE_SECTIONS}


def load_bundle(directory) -> Bundle | None:
    """The bundle at `directory`, or None when there is nothing to show.

    Returns rather than raises on an absent bundle: a checkout without one is a
    normal state, and a stack trace is a poor way to say so.
    """
    directory = Path(directory)
    index_path = directory / "index.json"
    if not index_path.exists():
        return None

    index = json.loads(index_path.read_text())
    sessions = []
    for entry in index.get("sessions", []):
        payload = json.loads(_within(directory, entry["file"]).read_text())
        counts = payload.get("counts") or {}
        sessions.append(Session(
            session_id=payload.get("session_id", entry.get("session_id", "")),
            event_stem=payload.get("event_stem", entry.get("event_stem", "")),
            started_at=payload.get("started_at", ""),
            ended_at=payload.get("ended_at", ""),
            # The counts are the bundle's own totals and are never recomputed
            # from the rows that shipped, because the incident rows are a
            # sample and a recomputed total would silently be the sample size.
            n_orders=int(counts.get("orders", 0)),
            n_fills=int(counts.get("fills", 0)),
            n_incidents=int(counts.get("incidents", 0)),
            note=payload.get("note", ""),
            limitations=tuple(payload.get("limitations", ())),
            sections=_readable(payload),
            incidents_are_a_sample=bool(payload.get("incidents_are_a_sample")),
        ))
    return Bundle(built_at=index.get("built_at", ""),
                  schema=int(index.get("schema", 0)),
                  sessions=tuple(sessions))
