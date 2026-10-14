"""Small deterministic analyses. No samples, macros or network calls execute."""

from __future__ import annotations

import csv
from email import policy
from email.parser import BytesHeaderParser
import io
import json
from pathlib import Path
import sqlite3
import struct
import tempfile
import zipfile

from .casefiles import evidence_bytes, load_case, verify
from .safeio import (ForgeError, MAX_JSON, MAX_RECORDS, atomic_write, digest,
                     json_bytes, require, safe_path, visible)
from .safeio import zip_directory_guard
from .timestamps import browser_timestamp, timestamp


def save_analysis(case: str | Path, output: str | Path, result: object) -> dict:
    root, _, _, _ = load_case(case)
    path = safe_path(output, exists=False)
    require(path.is_relative_to(root / "analysis"), "ANALYSIS_OUTPUT_REQUIRED")
    verify(root)
    data = json_bytes(result)
    require(len(data) <= MAX_JSON, "ANALYSIS_OUTPUT_TOO_LARGE")
    atomic_write(path, data)
    return {"status": "written", "sha256": digest(data)}


def triage(case: str | Path, identifier: str) -> dict:
    row, data = evidence_bytes(case, identifier)
    signatures = [(b"%PDF-", "pdf"), (b"\x89PNG\r\n\x1a\n", "png"),
                  (b"\xff\xd8\xff", "jpeg"), (b"PK\x03\x04", "zip"),
                  (b"SQLite format 3\x00", "sqlite"), (b"MZ", "pe_candidate"),
                  (b"\x7fELF", "elf_candidate")]
    kind = next((kind for magic, kind in signatures if data.startswith(magic)), "unknown")
    result = {"evidence_id": identifier, "size": len(data), "sha256": row["sha256"],
              "signature_family": kind, "executed": False, "limitations": []}
    if kind == "png":
        require(len(data) >= 33 and data[12:16] == b"IHDR", "INVALID_PNG_HEADER")
        width, height = struct.unpack(">II", data[16:24])
        require(width > 0 and height > 0, "INVALID_PNG_DIMENSIONS")
        result["dimensions"] = {"width": width, "height": height}
        result["limitations"].append("Header inspection only; pixels and metadata are not validated.")
    elif kind == "zip":
        zip_directory_guard(data, 1000)
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                entries = archive.infolist()
                require(len(entries) <= 1000, "ARCHIVE_TOO_MANY_ENTRIES")
                result["archive"] = {"entries": len(entries), "extracted": False,
                                     "declared_uncompressed_bytes": sum(e.file_size for e in entries),
                                     "unsafe_member_paths": sum(
                                         e.filename.startswith(("/", "\\"))
                                         or ".." in e.filename.replace("\\", "/").split("/")
                                         or ":" in e.filename for e in entries)}
        except (zipfile.BadZipFile, ValueError) as exc:
            raise ForgeError("INVALID_ZIP") from exc
        result["limitations"].append("Central-directory inspection only; members are never decompressed.")
    elif kind == "pdf":
        result["limitations"].append("PDF text, metadata, signatures and active content are not parsed.")
    elif kind == "jpeg":
        result["limitations"].append("JPEG signature only; EXIF and authenticity are not established.")
    elif kind == "unknown":
        # Header-only email parsing avoids attachments or active document content.
        if b"\nFrom:" in b"\n" + data[:65536] or b"\nReceived:" in b"\n" + data[:65536]:
            message = BytesHeaderParser(policy=policy.default).parsebytes(data[:65536])
            result["signature_family"] = "email_header_candidate"
            result["headers"] = {key: [visible(str(value), 1000) for value in message.get_all(key, [])][:30]
                                 for key in ("Date", "From", "To", "Subject", "Received",
                                             "Authentication-Results", "Message-ID")}
            result["limitations"].append("Headers may be forged; no delivery or sender authentication is established.")
        else:
            result["limitations"].append("Unknown format; request a trusted exported representation.")
    return result


def timeline(case: str | Path, identifier: str, format_name: str) -> dict:
    _, data = evidence_bytes(case, identifier)
    require(len(data) <= MAX_JSON, "STRUCTURED_INPUT_TOO_LARGE")
    try:
        text = data.decode("utf-8-sig")
        if format_name == "csv":
            rows = []
            for record in csv.DictReader(io.StringIO(text)):
                require(len(rows) < MAX_RECORDS, "TOO_MANY_RECORDS")
                rows.append(record)
        elif format_name == "jsonl":
            rows = []
            for line in io.StringIO(text):
                if line.strip():
                    require(len(rows) < MAX_RECORDS, "TOO_MANY_RECORDS")
                    rows.append(json.loads(line))
        else:
            value = json.loads(text)
            rows = value.get("events") if isinstance(value, dict) else value
    except (ValueError, UnicodeError, csv.Error, RecursionError) as exc:
        raise ForgeError("INVALID_TIMELINE_INPUT") from exc
    require(isinstance(rows, list) and len(rows) <= MAX_RECORDS, "INVALID_TIMELINE_ROWS")
    events = []
    for index, row in enumerate(rows):
        require(isinstance(row, dict), "INVALID_TIMELINE_ROW")
        event = row.get("event")
        require(isinstance(event, str) and 0 < len(event) <= 4000, "INVALID_EVENT_TEXT")
        require(row.get("timestamp") is None or isinstance(row["timestamp"], str),
                "INVALID_EVENT_TIMESTAMP")
        events.append({"evidence_id": identifier, "record_index": index,
                       "event": visible(event), **timestamp(row.get("timestamp"))})
    events.sort(key=lambda row: (row["utc"] is None, row["utc"] or "", row["record_index"]))
    return {"events": events, "event_count": len(events),
            "uncertain_time_count": sum(event["utc"] is None for event in events),
            "limitations": ["Order of events without an explicit offset remains unknown.",
                            "Source timestamps are statements, not verified clock measurements."]}


def timeline_csv(result: dict) -> bytes:
    fields = ["evidence_id", "record_index", "original_timestamp", "utc", "time_status", "event"]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for event in result["events"]:
        row = {}
        for key in fields:
            value = visible(event.get(key, "") or "")
            # Prevent spreadsheet formula execution; unmodified values remain in JSON.
            row[key] = "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def browser(case: str | Path, identifier: str) -> dict:
    _, data = evidence_bytes(case, identifier)
    require(data.startswith(b"SQLite format 3\x00"), "SQLITE_REQUIRED")
    result = {"evidence_id": identifier, "snapshot_completeness": "unverified",
              "limitations": ["A copied database without its WAL may be incomplete.",
                              "Recorded URLs do not prove user intent or page interaction."]}
    with tempfile.TemporaryDirectory(prefix="forge-browser-") as temporary:
        snapshot = Path(temporary) / "snapshot.sqlite"
        atomic_write(snapshot, data)
        try:
            connection = sqlite3.connect(snapshot.as_uri() + "?mode=ro&immutable=1", uri=True)
            try:
                connection.execute("PRAGMA trusted_schema=OFF")
                connection.execute("PRAGMA query_only=ON")
                # Bound queries even for pathological or deliberately corrupt DBs.
                ticks = [0]

                def progress():
                    ticks[0] += 1
                    return int(ticks[0] > 10000)

                connection.set_progress_handler(progress, 1000)
                tables = {row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1000")}
                if {"visits", "urls"} <= tables:
                    family, granularity = "chromium", "visit"
                    query = "SELECT u.url,u.title,v.visit_time FROM visits v JOIN urls u ON u.id=v.url ORDER BY v.visit_time,v.id LIMIT 5001"
                elif {"moz_places", "moz_historyvisits"} <= tables:
                    family, granularity = "firefox", "visit"
                    query = "SELECT p.url,p.title,h.visit_date FROM moz_historyvisits h JOIN moz_places p ON p.id=h.place_id ORDER BY h.visit_date,h.id LIMIT 5001"
                else:
                    raise ForgeError("UNSUPPORTED_BROWSER_SCHEMA")
                records = connection.execute(query).fetchall()
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise ForgeError("SQLITE_ANALYSIS_FAILED") from exc
    events = []
    for index, (url, title, moment) in enumerate(records[:MAX_RECORDS]):
        events.append({"evidence_id": identifier, "record_index": index,
                       "event": "browser visit", "url": visible(url, 2000),
                       "title": visible(title, 1000), **browser_timestamp(moment, family)})
    result.update({"family": family, "granularity": granularity, "events": events,
                   "event_count": len(events), "truncated": len(records) > MAX_RECORDS})
    return result
