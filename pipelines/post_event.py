#!/usr/bin/env python3
"""
CAGEBOT Post-Event Pipeline
============================
Processes results after a UFC event completes.

Steps:
    1. Fetch event HTML from UFCStats + cache
    2. Parse results → results.csv (with completeness gate)
    3. Update master_picks.csv with actual winners + finish details
    4. Generate missed picks analysis
    5. Rebuild fighter state (ELO + recency with new results)
    6. Run post-event agent (Claude-powered miss analysis)
    7. Update master_events.csv (status=completed, accuracy metrics)
    8. Post results card to Discord

Design principles:
    - Completeness gate: if results.csv has fewer fights than picks.csv,
      the pipeline returns False and retries on next cron tick
    - Atomic writes: all master file updates use temp + os.replace()
    - Failure alerting: RED alert to Discord on any step failure
    - Idempotent: safe to re-run after partial failure

Usage:
    PYTHONPATH=. python pipelines/post_event.py --event-stem UFC_2026_04_11
    PYTHONPATH=. python pipelines/post_event.py  # auto-detects post-event
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


def run(event_stem: str) -> bool:
    """Run the complete post-event pipeline. Returns True on success.

    The pipeline has a hard gate at Step 2: if the parsed results
    are incomplete (fewer fights than expected), the pipeline returns
    False without modifying any master files. The scheduler retries
    every 4 hours on Sat/Sun until results are complete.
    """
    year = event_stem.split("_")[1]
    event_dir = ROOT / "data" / "processed" / year / event_stem

    # Load event metadata
    meta_path = event_dir / "event_metadata.json"
    event_name = event_stem.replace("_", " ")
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
            event_name = meta.get("event_name", event_name)
        except Exception:
            pass

    _log(f"Post-event pipeline: {event_name} ({event_stem})")
    _log("=" * 60)

    steps_ok = 0
    errors = []

    # ── Step 1: Fetch + cache UFCStats HTML ──────────────────────────
    _log("Step 1/8: Fetching UFCStats HTML")
    # [SCRAPING LOGIC — uses cached HTML to avoid re-fetching]
    steps_ok += 1

    # ── Step 2: Parse results → results.csv ──────────────────────────
    _log("Step 2/8: Parsing results")
    # [PARSING LOGIC — extracts winner, method, round, time from HTML]
    # HARD GATE: if results are incomplete, return False
    # The scheduler will retry on the next cron tick
    steps_ok += 1

    # ── Step 3: Update master_picks.csv ──────────────────────────────
    _log("Step 3/8: Updating master_picks with results")
    # Matches results.csv rows to master_picks by event_stem + fight name
    # Updates: actual_winner, model_correct, finish_method, finish_round
    # Atomic write: writes to .csv.tmp then os.replace()
    steps_ok += 1

    # ── Step 4: Generate missed picks analysis ───────────────────────
    _log("Step 4/8: Generating missed picks analysis")
    if _run_script("generate_missed_picks_analysis.py", ["--event", event_stem],
                   "Missed picks analysis"):
        steps_ok += 1
    else:
        errors.append("Step 4: missed picks analysis failed (non-critical)")

    # ── Step 5: Rebuild fighter state ────────────────────────────────
    _log("Step 5/8: Rebuilding fighter state")
    try:
        from scripts.compute_fighter_state import rebuild
        rebuild()
        _log("  Fighter state rebuilt with new results")
        steps_ok += 1
    except Exception as e:
        _log(f"  Fighter state rebuild: {e}", "ERROR")
        errors.append(f"Step 5: {e}")

    # ── Step 6: Post-event agent (Claude miss analysis) ──────────────
    _log("Step 6/8: Running post-event agent")
    if _run_script("agents/post_event_agent.py", ["--event", event_stem],
                   "Post-event agent"):
        steps_ok += 1
    else:
        errors.append("Step 6: post-event agent failed (non-critical)")

    # ── Step 7: Update master_events.csv ─────────────────────────────
    _log("Step 7/8: Updating master_events")
    # Sets status=completed, computes model_correct, combined_correct,
    # override stats, avg_model_prob, avg_market_implied
    # Atomic write
    steps_ok += 1

    # ── Step 8: Post results to Discord ──────────────────────────────
    _log("Step 8/8: Posting results to Discord")
    # [DISCORD WEBHOOK LOGIC REMOVED]
    steps_ok += 1

    # ── Summary ──────────────────────────────────────────────────────
    _log(f"\nPipeline complete: {steps_ok}/8 steps OK")
    if errors:
        _log(f"Errors: {', '.join(errors)}", "WARN")
        _alert(event_name, f"Post-event issues: {', '.join(errors)}")

    return len(errors) == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CAGEBOT post-event pipeline")
    parser.add_argument("--event-stem", help="Event stem (e.g., UFC_2026_04_11)")
    args = parser.parse_args()

    if args.event_stem:
        success = run(args.event_stem)
    else:
        from scripts.path_utils import detect_post_event, PROCESSED_DIR
        detected = detect_post_event(PROCESSED_DIR)
        if detected:
            success = run(detected)
        else:
            print("No post-event detected.")
            success = False

    sys.exit(0 if success else 1)
