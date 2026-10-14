#!/usr/bin/env python3
"""Create and verify an original synthetic case without network/model calls."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
from forgekit.analysis import browser, save_analysis, timeline
from forgekit.casefiles import add_claim, add_evidence, initialize, provenance, verify
from forgekit.reporting import export_case, prepare_share, render_report, restore_case, verify_export
from forgekit.safeio import ForgeError, atomic_write, json_bytes, read_bytes, require, safe_path


def chromium_fixture(path: Path) -> None:
    epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
    moment = datetime(2026, 10, 1, 8, 5, tzinfo=timezone.utc) - epoch
    encoded = (moment.days * 86400 + moment.seconds) * 1000000 + moment.microseconds
    connection = sqlite3.connect(path)
    try:
        connection.executescript("CREATE TABLE urls(id INTEGER PRIMARY KEY,url TEXT,title TEXT);"
                                 "CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER,visit_time INTEGER);")
        connection.execute("INSERT INTO urls VALUES(1,?,?)", ("https://outlet-a.invalid/bulletin", "Synthetic bulletin"))
        connection.execute("INSERT INTO visits VALUES(1,1,?)", (encoded,))
        connection.commit()
    finally:
        connection.close()


def demo(destination: str | Path) -> dict:
    base = safe_path(destination, exists=False)
    require(not base.exists(), "OUTPUT_EXISTS")
    safe_path(base.parent)
    base.mkdir(mode=0o700)
    inputs = base / "inputs"
    inputs.mkdir(mode=0o700)
    for source in sorted((ROOT / "examples" / "inputs").iterdir()):
        atomic_write(inputs / source.name, read_bytes(source))
    chromium_fixture(inputs / "history.sqlite")
    case = base / "case"
    initialize(case, "Synthetic Dock 7 investigation", "Offline examination of original synthetic fixtures only")
    for name in ("article-a.json", "article-b.json", "article-c.json"):
        add_evidence(case, inputs / name, origin_group="harbor-bulletin")
    event = add_evidence(case, inputs / "events.json")
    history = add_evidence(case, inputs / "history.sqlite")
    add_evidence(case, inputs / "untrusted-note.txt")
    add_evidence(case, inputs / "media-metadata.json")
    add_claim(case, "The three articles attribute their closure statement to the Harbor Bulletin.",
              ["E000001", "E000002", "E000003"], [], "observed", "high",
              "Each literal capture names the same attribution; this is not three independent event witnesses.")
    add_claim(case, "The closure began at 09:00 UTC.", [], [event["id"]], "unconfirmed", "low",
              "The bulletin's event time has no offset, and captured status does not establish execution of the planned closure.")
    events = timeline(case, event["id"], "json")
    events["input"] = {"evidence_id": event["id"], "sha256": event["sha256"]}
    save_analysis(case, case / "analysis" / "timeline.json", events)
    visits = browser(case, history["id"])
    visits["input"] = {"evidence_id": history["id"], "sha256": history["sha256"]}
    save_analysis(case, case / "analysis" / "browser.json", visits)
    for language in ("en", "fr"):
        atomic_write(case / "reports" / f"report.{language}.md", render_report(case, language))
    private = case / "exports" / "private.zip"
    export_case(case, private, "private")
    verify_export(private)
    restore_case(private, base / "resumed-case")
    share = prepare_share(case / "reports" / "report.en.md", case / "exports" / "review-draft.md")
    summary = {"status": "passed", "synthetic_only": True,
               "verified": verify(case), "provenance": provenance(case),
               "uncertain_timestamps": events["uncertain_time_count"],
               "resumed": verify(base / "resumed-case"), "public_view_status": share["status"],
               "public_export": "not_created_without_human_review", "model_trial": "not_run"}
    atomic_write(base / "summary.json", json_bytes(summary))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(demo(args.out), sort_keys=True))
    except (ForgeError, OSError, ValueError, sqlite3.Error) as exc:
        print(json.dumps({"status": "error", "code": str(exc) if isinstance(exc, ForgeError) else "DEMO_IO_ERROR"}))
        raise SystemExit(2)
