from __future__ import annotations

import csv
from datetime import datetime, timezone
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

BROWSER_URL_BYTES = 16 * 1024
BROWSER_TITLE_BYTES = 8 * 1024
BROWSER_ROW_BYTES = 32 * 1024


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
    events.sort(key=lambda row: (row["utc"] is None,
                datetime.fromisoformat(row["utc"]) if row["utc"] else datetime.max.replace(tzinfo=timezone.utc),
                row["record_index"]))
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
            value = event.get(key)
            value = visible("" if value is None else value)
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
                connection.execute("PRAGMA temp_store=FILE")
                connection.execute("PRAGMA cache_size=-2048")
                connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, BROWSER_ROW_BYTES)
                ticks = [0]

                def progress():
                    ticks[0] += 1
                    return int(ticks[0] > 10000)

                connection.set_progress_handler(progress, 1000)
                tables = {row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1000")}
                if {"visits", "urls"} <= tables:
                    family, granularity = "chromium", "visit"
                    query = "SELECT url,visit_time FROM visits ORDER BY visit_time,id LIMIT 5001"
                    lookup = "SELECT url,title FROM urls WHERE id=? LIMIT 2"
                elif {"moz_places", "moz_historyvisits"} <= tables:
                    family, granularity = "firefox", "visit"
                    query = "SELECT place_id,visit_date FROM moz_historyvisits ORDER BY visit_date,id LIMIT 5001"
                    lookup = "SELECT url,title FROM moz_places WHERE id=? LIMIT 2"
                else:
                    raise ForgeError("UNSUPPORTED_BROWSER_SCHEMA")
                events = []
                output_bytes = len(json_bytes(result)) + 1024
                truncated = False
                for index, (place, moment) in enumerate(connection.execute(query)):
                    if index == MAX_RECORDS:
                        truncated = True
                        break
                    require(type(place) is int, "INVALID_BROWSER_ROW")
                    cursor = connection.execute(lookup, (place,))
                    fields = cursor.fetchone()
                    require(fields is not None and cursor.fetchone() is None, "INVALID_BROWSER_REFERENCE")
                    url, title = fields
                    require(isinstance(url, str) and (title is None or isinstance(title, str))
                            and type(moment) is int, "INVALID_BROWSER_ROW")
                    title = title or ""
                    require(len(url.encode("utf-8")) <= BROWSER_URL_BYTES
                            and len(title.encode("utf-8")) <= BROWSER_TITLE_BYTES,
                            "BROWSER_FIELD_TOO_LARGE")
                    event = {"evidence_id": identifier, "record_index": index,
                             "event": "browser visit", "url": url, "url_exact": True,
                             "title": visible(title, 1000), "title_truncated": len(title) > 1000,
                             **browser_timestamp(moment, family)}
                    output_bytes += len(json_bytes(event)) + 128
                    require(output_bytes <= MAX_JSON, "ANALYSIS_OUTPUT_TOO_LARGE")
                    events.append(event)
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise ForgeError("SQLITE_ANALYSIS_FAILED") from exc
    result.update({"family": family, "granularity": granularity, "events": events,
                   "event_count": len(events), "truncated": truncated})
    return result
