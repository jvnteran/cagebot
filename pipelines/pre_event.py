#!/usr/bin/env python3
"""
CAGEBOT Pre-Event Pipeline
============================
Single entry point for all Monday pre-event processing.

Steps:
    1. Rebuild fighter state (ELO + recency)
    2. Fetch TheOddsAPI odds (multibook — 5 sportsbooks)
    3. Run V2.4 predictions — aborts if no odds available
    4. Scrape ESPN fighter profiles (non-critical)
    5. Run intuition agent (scenario analysis + override signals)
    6. Run risk assessment check
    7. Append assessment to master
    8. Ingest picks to master_picks.csv (idempotent, atomic write)
    9. Ingest picks + MOV to workbook (non-critical)
    10. Post picks card to Discord

Usage:
    PYTHONPATH=. python pipelines/pre_event.py --event-stem UFC_2026_04_11
    PYTHONPATH=. python pipelines/pre_event.py  # auto-detects next upcoming
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _log(msg: str, level: str = "INFO"):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def _run_script(script: str, args: list[str], label: str) -> bool:
    """Run a script as subprocess. Returns True on success."""
    cmd = [sys.executable, str(ROOT / "scripts" / script)] + args
    _log(f"  Running: {label}")
    try:
        result = subprocess.run(
            cmd, cwd=ROOT,
            env={**__import__("os").environ, "PYTHONPATH": str(ROOT)},
            capture_output=True, text=True, timeout=600,
        )
        if result.returncode == 0:
            _log(f"  {label} — OK")
            return True
        _log(f"  {label} failed: {result.stderr[-2000:]}", "ERROR")
        return False
    except subprocess.TimeoutExpired:
        _log(f"  {label} timed out (600s)", "ERROR")
        return False
    except Exception as e:
        _log(f"  {label}: {e}", "ERROR")
        return False


def _alert(event_name: str, message: str):
    """Send failure alert to Discord."""
    try:
        from scripts.discord_notify import notify_pipeline_failure
        notify_pipeline_failure(event_name, message)
    except Exception:
        pass


def run(event_stem: str, ufcstats_url: str = None) -> bool:
    """Run the complete pre-event pipeline. Returns True on success.

    Pipeline is designed to be:
    - Idempotent: safe to re-run if a step fails
    - Fail-fast: aborts on critical failures (no odds, no predictions)
    - Resilient: non-critical steps (ESPN, intuition) continue on failure
    - Observable: every step logs success/failure, Discord alerts on abort
    """
    year = event_stem.split("_")[1]
    event_dir = ROOT / "data" / "processed" / year / event_stem
    picks_path = event_dir / "picks.csv"

    # Load event metadata
    meta_path = event_dir / "event_metadata.json"
    event_name = event_stem.replace("_", " ")
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
            event_name = meta.get("event_name", event_name)
            ufcstats_url = ufcstats_url or meta.get("ufcstats_url")
        except Exception:
            pass

    _log(f"Pre-event pipeline: {event_name} ({event_stem})")
    _log("=" * 60)

    steps_ok = 0
    errors = []

    # ── Step 1: Rebuild fighter state (ELO + recency) ──────────────────
    _log("Step 1/10: Rebuilding fighter state")
    try:
        from scripts.compute_fighter_state import rebuild
        rebuild()
        _log("  Fighter state rebuilt")
        steps_ok += 1
    except Exception as e:
        _log(f"  Fighter state: {e}", "ERROR")
        errors.append(f"Step 1: {e}")

    # ── Step 2: Fetch odds (TheOddsAPI multibook) ──────────────────────
    _log("Step 2/10: Fetching odds")
    if _run_script("fetch_odds.py", ["--event", event_stem], "Fetch odds"):
        steps_ok += 1
    else:
        errors.append("Step 2: Odds fetch failed")

    # ── Step 3: Run V2.4 predictions (REQUIRES odds) ──────────────────
    _log("Step 3/10: Running V2.4 predictions")
    # [MODEL INFERENCE LOGIC REMOVED — proprietary]
    # Calls setup_event.py with the UFCStats URL to generate picks.csv
    # Aborts if odds are unavailable (V2.4 requires market data)
    steps_ok += 1

    # ── Step 4: Scrape ESPN profiles (non-critical) ───────────────────
    _log("Step 4/10: Scraping ESPN fighter profiles")
    if _run_script("scrape_espn_profiles.py", ["--event", event_stem], "ESPN profiles"):
        steps_ok += 1
    else:
        errors.append("Step 4: ESPN profiles failed (non-critical)")

    # ── Step 5: Run intuition agent (non-critical) ────────────────────
    _log("Step 5/10: Running intuition agent")
    if _run_script("agents/intuition_agent.py", ["--event", event_stem], "Intuition agent"):
        steps_ok += 1
    else:
        errors.append("Step 5: Intuition agent failed (non-critical)")

    # ── Step 6: Run risk assessment ───────────────────────────────────
    _log("Step 6/10: Running risk assessment")
    # [ASSESSMENT LOGIC REMOVED — proprietary thresholds]
    steps_ok += 1

    # ── Step 7: Append assessment to master ───────────────────────────
    _log("Step 7/10: Appending to master")
    steps_ok += 1

    # ── Step 8: Ingest picks to master_picks.csv ─────────────────────
    _log("Step 8/10: Ingesting picks to master_picks.csv")
    # Reads official_picks CSV, maps to master_picks schema,
    # removes existing rows for this event (idempotent),
    # atomic write via temp file + os.replace()
    steps_ok += 1

    # ── Step 9: Ingest to workbook (non-critical) ────────────────────
    _log("Step 9/10: Ingesting to workbook")
    if _run_script("agents/workbook_agent.py", ["--event", event_stem], "Workbook agent"):
        steps_ok += 1
    else:
        errors.append("Step 9: Workbook agent failed (non-critical)")

    # ── Step 10: Post picks card to Discord ──────────────────────────
    _log("Step 10/10: Posting picks to Discord")
    # [DISCORD WEBHOOK LOGIC REMOVED]
    steps_ok += 1

    # ── Summary ──────────────────────────────────────────────────────
    _log(f"\nPipeline complete: {steps_ok}/10 steps OK")
    if errors:
        _log(f"Errors: {', '.join(errors)}", "WARN")
        _alert(event_name, f"Pre-event partial: {steps_ok}/10 — {', '.join(errors)}")

    return len(errors) == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CAGEBOT pre-event pipeline")
    parser.add_argument("--event-stem", help="Event stem (e.g., UFC_2026_04_11)")
    args = parser.parse_args()

    if args.event_stem:
        success = run(args.event_stem)
    else:
        # Auto-detect next upcoming event
        from scripts.path_utils import detect_upcoming_event, PROCESSED_DIR
        detected = detect_upcoming_event(PROCESSED_DIR)
        if detected:
            success = run(detected)
        else:
            print("No upcoming event detected.")
            success = False

    sys.exit(0 if success else 1)
