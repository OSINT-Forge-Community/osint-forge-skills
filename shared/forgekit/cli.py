from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import sys

from . import VERSION
from .analysis import browser, save_analysis, timeline, timeline_csv, triage
from .casefiles import (add_claim, add_evidence, add_many, evidence_bytes, initialize,
                        load_case, provenance, verify)
from .reporting import (export_case, prepare_share, render_report, restore_case,
                        verify_export)
from .safeio import (ForgeError, MAX_FILE, MAX_JSON, MAX_RECORDS, MAX_TOTAL,
                     atomic_write, digest, json_bytes, read_json, require, safe_path)
from .timestamps import timestamp
from .tooling import TOOLS, inventory, run_tool


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ForgeError("INVALID_ARGUMENTS")


def parser() -> argparse.ArgumentParser:
    root = Parser(description="Offline evidence utilities. Originals are never executed.")
    root.add_argument("--version", action="version", version=VERSION)
    commands = root.add_subparsers(dest="command", required=True, parser_class=Parser)
    start = commands.add_parser("init", help="Create a new private case directory")
    start.add_argument("--case", required=True)
    start.add_argument("--title", required=True)
    start.add_argument("--scope", required=True)
    add = commands.add_parser("add", help="Copy one explicitly selected evidence file")
    add.add_argument("--case", required=True)
    add.add_argument("--source", required=True)
    add.add_argument("--url", help="HTTPS provenance URL without credentials, query or fragment")
    add.add_argument("--origin-group", help="Analyst label; not an independence assertion")
    batch = commands.add_parser("add-many", help="Copy explicitly selected files under one case lock")
    batch.add_argument("--case", required=True)
    batch.add_argument("--source", action="append", required=True)
    batch.add_argument("--url", help="Shared HTTPS provenance URL without credentials, query or fragment")
    batch.add_argument("--origin-group", help="Shared analyst origin label")
    claim = commands.add_parser("claim", help="Record an analyst claim with evidence references")
    claim.add_argument("--case", required=True)
    claim.add_argument("--text", required=True)
    claim.add_argument("--support", action="append", default=[])
    claim.add_argument("--contradict", action="append", default=[])
    claim.add_argument("--state", choices=("observed", "inferred", "unconfirmed"), required=True)
    claim.add_argument("--confidence", choices=("low", "medium", "high"), default="low")
    claim.add_argument("--rationale", required=True)
    for name in ("verify", "provenance"):
        child = commands.add_parser(name)
        child.add_argument("--case", required=True)
    for name in ("triage", "timeline", "browser"):
        child = commands.add_parser(name)
        child.add_argument("--case", required=True)
        child.add_argument("--evidence", required=True)
        child.add_argument("--out", required=True, help="A new file inside CASE/analysis")
        if name == "timeline":
            child.add_argument("--format", choices=("json", "jsonl", "csv"), default="json")
            child.add_argument("--csv", help="Optional new CSV file inside CASE/analysis")
    report = commands.add_parser("report")
    report.add_argument("--case", required=True)
    report.add_argument("--lang", choices=("en", "fr"), default="en")
    report.add_argument("--replace", action="store_true", help="Replace only the fixed generated report")
    share = commands.add_parser("prepare-share")
    share.add_argument("--input", required=True)
    share.add_argument("--out", required=True)
    export = commands.add_parser("export")
    export.add_argument("--case", required=True)
    export.add_argument("--out", required=True)
    export.add_argument("--mode", choices=("private", "public"), required=True)
    export.add_argument("--view")
    export.add_argument("--approved-sha256")
    checker = commands.add_parser("verify-export")
    checker.add_argument("--archive", required=True)
    restore = commands.add_parser("restore")
    restore.add_argument("--archive", required=True)
    restore.add_argument("--case", required=True)
    correlate = commands.add_parser("correlate")
    correlate.add_argument("--case", required=True)
    correlate.add_argument("--input", action="append", required=True)
    correlate.add_argument("--out", required=True)
    commands.add_parser("doctor", help="Report local runtime capabilities without collecting evidence")
    commands.add_parser("tools", help="Find optional local tools without executing or installing them")
    external = commands.add_parser("tool-run", help="Run an explicitly selected local tool on an evidence copy")
    external.add_argument("--case", required=True)
    external.add_argument("--evidence", required=True)
    external.add_argument("--tool", required=True, choices=tuple(TOOLS))
    external.add_argument("--executable", required=True, help="Approved absolute executable path")
    external.add_argument("--out", required=True, help="A new JSON file inside CASE/analysis")
    external.add_argument("--first-page", type=int, default=1)
    external.add_argument("--last-page", type=int, default=1)
    external.add_argument("--language", default="eng", help="Installed OCR language, for example eng or fra+eng")
    return root


def correlate(case: str, paths: list[str]) -> dict:
    verify(case)
    root, _, evidence, _ = load_case(case)
    indexed = {row["id"]: row for row in evidence}
    require(2 <= len(paths) <= 20 and len(set(paths)) == len(paths), "INVALID_CORRELATION_INPUTS")
    candidates = {}
    count = 0
    skipped_urls = 0
    for index, value in enumerate(paths):
        path = safe_path(value)
        require(path.is_relative_to(root / "analysis"), "ANALYSIS_INPUT_REQUIRED")
        data = read_json(path)
        require(isinstance(data, dict) and isinstance(data.get("input"), dict),
                "ANALYSIS_PROVENANCE_MISSING")
        source = data["input"]
        require(source.get("evidence_id") in indexed
                and source.get("sha256") == indexed[source["evidence_id"]]["sha256"],
                "ANALYSIS_PROVENANCE_MISMATCH")
        events = data.get("events")
        require(isinstance(events, list), "EVENT_ANALYSIS_REQUIRED")
        for event in events:
            require(isinstance(event, dict) and event.get("evidence_id") == source["evidence_id"],
                    "INVALID_EVENT_REFERENCE")
            count += 1
            require(count <= MAX_RECORDS, "TOO_MANY_EVENTS")
            url = event.get("url") if event.get("url_exact") is True else None
            skipped_urls += int(bool(event.get("url")) and url is None)
            moment = timestamp(event.get("utc"))["utc"]
            for kind, key in (("same_utc", moment), ("same_url", url)):
                if isinstance(key, str) and key:
                    candidates.setdefault((kind, key), []).append({"input_index": index,
                        "evidence_id": source["evidence_id"], "record_index": event.get("record_index")})
    groups = [{"basis": kind, "value": key, "records": records,
               "interpretation": "candidate_link_requires_analyst_review"}
              for (kind, key), records in sorted(candidates.items())
              if len({row["input_index"] for row in records}) > 1]
    return {"candidate_links": groups, "candidate_count": len(groups),
            "skipped_unverified_url_count": skipped_urls,
            "limitations": ["A shared timestamp or URL does not establish identity, causation or independence.",
                            "Regenerate legacy browser analyses to correlate exact URLs.",
                            "Derived metadata can be edited; reproduce the analyses before relying on them."]}


def dispatch(args) -> dict:
    command = args.command
    if command == "tools":
        return inventory()
    if command == "tool-run":
        require(args.tool == "pdftotext" or (args.first_page == 1 and args.last_page == 1),
                "INVALID_ARGUMENTS")
        require(args.tool == "tesseract" or args.language == "eng", "INVALID_ARGUMENTS")
        return run_tool(args.case, args.evidence, args.tool, args.executable, args.out,
                        first_page=args.first_page, last_page=args.last_page, language=args.language)
    if command == "init":
        return initialize(args.case, args.title, args.scope)
    if command == "add":
        return add_evidence(args.case, args.source, source_url=args.url, origin_group=args.origin_group)
    if command == "add-many":
        return add_many(args.case, args.source, source_url=args.url, origin_group=args.origin_group)
    if command == "claim":
        return add_claim(args.case, args.text, args.support, args.contradict,
                         args.state, args.confidence, args.rationale)
    if command in ("verify", "provenance"):
        return (verify if command == "verify" else provenance)(args.case)
    if command in ("triage", "timeline", "browser"):
        if command == "triage":
            result = triage(args.case, args.evidence)
        elif command == "browser":
            result = browser(args.case, args.evidence)
        else:
            result = timeline(args.case, args.evidence, args.format)
        evidence, _ = evidence_bytes(args.case, args.evidence)
        result["input"] = {"evidence_id": evidence["id"], "sha256": evidence["sha256"]}
        if command == "timeline" and args.csv:
            root, _, _, _ = load_case(args.case)
            destination = safe_path(args.csv, exists=False)
            require(destination.is_relative_to(root / "analysis"), "ANALYSIS_OUTPUT_REQUIRED")
            require(not destination.exists() and destination != safe_path(args.out, exists=False),
                    "OUTPUT_EXISTS")
        saved = save_analysis(args.case, args.out, result)
        if command == "timeline" and args.csv:
            atomic_write(args.csv, timeline_csv(result))
        return {**saved, "evidence_id": args.evidence,
                "event_count": result.get("event_count", 0)}
    if command == "report":
        root, _, _, _ = load_case(args.case)
        data = render_report(args.case, args.lang)
        atomic_write(root / "reports" / f"report.{args.lang}.md", data, replace=args.replace)
        return {"status": "written", "sha256": digest(data), "language": args.lang}
    if command == "prepare-share":
        return prepare_share(args.input, args.out)
    if command == "export":
        return export_case(args.case, args.out, args.mode, args.view, args.approved_sha256)
    if command == "verify-export":
        return verify_export(args.archive)
    if command == "restore":
        return restore_case(args.archive, args.case)
    if command == "correlate":
        return save_analysis(args.case, args.out, correlate(args.case, args.input))
    return {"version": VERSION, "python": platform.python_version(),
            "network_calls": False, "optional_packages_required": False,
            "limits": {"file_bytes": MAX_FILE, "case_bytes": MAX_TOTAL,
                       "structured_bytes": MAX_JSON, "records": MAX_RECORDS},
            "formats": ["json", "jsonl", "csv", "chromium_history", "firefox_history",
                        "file_signatures", "email_headers", "png_dimensions"],
            "unsupported": ["disk_acquisition", "memory_acquisition", "evtx_binary",
                            "pdf_text", "exif_extraction", "media_authenticity_classification"],
            "host_agent_permissions": "not_controlled_by_these_helpers"}


def main(argv: list[str] | None = None) -> int:
    try:
        result = dispatch(parser().parse_args(argv))
    except ForgeError as exc:
        print(json.dumps({"status": "error", "code": str(exc)}))
        return 2
    except (OSError, UnicodeError, ValueError, TypeError, OverflowError, RecursionError):
        print(json.dumps({"status": "error", "code": "IO_OR_FORMAT_ERROR"}))
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
