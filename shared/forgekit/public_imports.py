from __future__ import annotations

from datetime import date, datetime
import json
import re
from urllib.parse import urlsplit

from .exchange import source
from .safeio import ForgeError, MAX_JSON, MAX_RECORDS, checkpoint, json_bytes, require
from .snapshot import read_operation


def field(value, code, maximum=4000):
    require(isinstance(value, str) and 0 < len(value) <= maximum and "\x00" not in value, code)
    return value


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result

    try:
        return json.loads(text, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ForgeError("INVALID_IMPORT_JSON") from exc


def public_url(value):
    field(value, "INVALID_IMPORT_URL", 8192)
    require(not any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value)
            and "\\" not in value, "INVALID_IMPORT_URL")
    try:
        parts = urlsplit(value)
        require(parts.scheme in ("http", "https") and bool(parts.hostname)
                and parts.username is None and parts.password is None, "INVALID_IMPORT_URL")
        parts.port
    except ValueError as exc:
        raise ForgeError("INVALID_IMPORT_URL") from exc
    return value


def calendar_date(value):
    require(isinstance(value, str) and bool(re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value)),
            "INVALID_IMPORT_DATE")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ForgeError("INVALID_IMPORT_DATE") from exc
    return value


def result(kind, provenance, events, limitations, **details):
    value = {"analysis_type": kind, "input": provenance, "events": events,
             "event_count": len(events), "network_calls": False,
             "authenticity": "not_established", "limitations": limitations, **details}
    require(len(json_bytes(value)) <= MAX_JSON, "ANALYSIS_OUTPUT_TOO_LARGE")
    return value


@read_operation
def wayback_index(case, identifier, url, after=None, before=None):
    public_url(url)
    if after is not None:
        calendar_date(after)
    if before is not None:
        calendar_date(before)
    require(after is None or before is None or after <= before, "INVALID_DATE_WINDOW")
    provenance, data = source(case, identifier)
    rows = strict_json(data)
    require(isinstance(rows, list) and len(rows) <= MAX_RECORDS + 1, "INVALID_CDX_ROWS")
    if rows:
        headers = rows[0]
        require(isinstance(headers, list) and all(isinstance(key, str) for key in headers)
                and len(set(headers)) == len(headers)
                and {"timestamp", "original"} <= set(headers), "INVALID_CDX_HEADERS")
    events = []
    for index, values in enumerate(rows[1:]):
        checkpoint()
        require(isinstance(values, list) and len(values) == len(headers)
                and all(isinstance(value, str) for value in values), "INVALID_CDX_ROW")
        row = dict(zip(headers, values))
        moment = row["timestamp"]
        require(bool(re.fullmatch(r"[0-9]{14}", moment)), "INVALID_CDX_TIMESTAMP")
        try:
            parsed = datetime.strptime(moment, "%Y%m%d%H%M%S")
        except ValueError as exc:
            raise ForgeError("INVALID_CDX_TIMESTAMP") from exc
        original = public_url(row["original"])
        day = parsed.date().isoformat()
        if original != url or after is not None and day < after or before is not None and day > before:
            continue
        events.append({"evidence_id": identifier, "record_index": index,
                       "source_row": index + 1, "event": "Capture listed in supplied CDX index",
                       "url": original, "original_timestamp": moment,
                       "utc": parsed.isoformat() + "Z", "time_status": "explicit_utc",
                       "capture_timestamp": moment, "cdx": row})
    events.sort(key=lambda row: (row["capture_timestamp"], row["record_index"]))
    return result("wayback_cdx", provenance, events,
                  ["An index entry does not establish capture availability or page contents.",
                   "Missing captures do not prove absence. Digests are supplied index values, not authenticity proof.",
                   "Only the supplied index is searched. No capture is fetched or saved online."],
                  selection={"url": url, "after": after, "before": before},
                  supplied_records=max(0, len(rows) - 1), coverage="supplied_export_only")


def siren_value(value):
    require(isinstance(value, str), "INVALID_SIREN")
    normalized = value.replace(" ", "").replace("\u00a0", "")
    require(bool(re.fullmatch(r"[0-9]{9}", normalized)), "INVALID_SIREN")
    return normalized


@read_operation
def bodacc_history(case, identifier, siren, event_date_field=None):
    selected = siren_value(siren)
    require(event_date_field is None or isinstance(event_date_field, str)
            and bool(re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,63}", event_date_field))
            and event_date_field != "dateparution", "INVALID_EVENT_DATE_FIELD")
    provenance, data = source(case, identifier)
    value = strict_json(data)
    total = None
    if isinstance(value, dict):
        rows = value.get("results")
        total = value.get("total_count")
        require(total is None or type(total) is int and total >= 0, "INVALID_BODACC_TOTAL")
    else:
        rows = value
    require(isinstance(rows, list) and len(rows) <= MAX_RECORDS
            and (total is None or total >= len(rows)), "INVALID_BODACC_ROWS")
    events, missing_register = [], 0
    for index, row in enumerate(rows):
        checkpoint()
        require(isinstance(row, dict), "INVALID_BODACC_ROW")
        registers = row.get("registre")
        if registers is None or registers == [] or registers == "":
            missing_register += 1
            continue
        if isinstance(registers, str):
            registers = [registers]
        require(isinstance(registers, list), "INVALID_BODACC_REGISTER")
        normalized = [siren_value(item) for item in registers]
        if selected not in normalized:
            continue
        notice = field(row.get("id"), "INVALID_BODACC_ID", 200)
        publication = calendar_date(row.get("dateparution"))
        effective = row.get(event_date_field) if event_date_field else None
        if effective is not None:
            effective = calendar_date(effective)
        family = row.get("familleavis_lib") or "Notice"
        field(family, "INVALID_BODACC_FAMILY", 1000)
        events.append({"evidence_id": identifier, "record_index": index,
                       "event": "BODACC publication: " + family,
                       "notice_id": notice, "siren": selected, "notice": row,
                       "publication_date": publication, "event_date": effective,
                       "event_date_status": "supplied_field" if effective else "unknown",
                       "original_timestamp": publication, "utc": None, "time_status": "date_only"})
    events.sort(key=lambda row: (row["publication_date"], row["record_index"]))
    return result("bodacc_history", provenance, events,
                  ["Order is by publication date, not the effective date of the announced act.",
                   "A date has no invented time or timezone. Missing event dates remain unknown.",
                   "SIREN matching is textual after spacing normalization, not registry or identity verification.",
                   "Supplied records do not establish current ownership or complete company history."],
                  selection={"siren": selected, "event_date_field": event_date_field},
                  supplied_records=len(rows), source_total_count=total,
                  rows_without_register=missing_register,
                  coverage="partial_export" if total is not None and total > len(rows) else "supplied_export_only")


def cue_time(value, format_name):
    pattern = (r"([0-9]{2,4}):([0-9]{2}):([0-9]{2}),([0-9]{3})" if format_name == "srt"
               else r"(?:([0-9]{2,4}):)?([0-9]{2}):([0-9]{2})\.([0-9]{3})")
    match = re.fullmatch(pattern, value)
    require(match is not None, "INVALID_CUE_TIME")
    hours, minutes, seconds, milliseconds = [int(part or 0) for part in match.groups()]
    require(hours <= 9999 and minutes < 60 and seconds < 60, "INVALID_CUE_TIME")
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + milliseconds


def transcript_excerpt(derived, start, end):
    events = derived.get("events")
    require(isinstance(events, list) and 0 < len(events) <= MAX_RECORDS,
            "CITATION_FORMAT_UNSUPPORTED")
    selected = []
    for row in events:
        checkpoint()
        require(isinstance(row, dict) and type(row.get("start_ms")) is int
                and type(row.get("end_ms")) is int and 0 <= row["start_ms"] < row["end_ms"]
                and isinstance(row.get("event"), str), "CITATION_FORMAT_UNSUPPORTED")
        if row["start_ms"] < end and row["end_ms"] > start:
            selected.append(row)
    require(bool(selected) and min(row["start_ms"] for row in selected) == start
            and max(row["end_ms"] for row in selected) == end, "CITATION_RANGE_MISMATCH")
    return "\n".join(row["event"] for row in selected)


@read_operation
def transcript(case, identifier, format_name, method="unknown", translation="unknown", language=None):
    require(format_name in ("srt", "vtt"), "INVALID_TRANSCRIPT_FORMAT")
    require(method in ("unknown", "manual", "automatic"), "INVALID_TRANSCRIPT_METHOD")
    require(translation in ("unknown", "original", "translated"), "INVALID_TRANSLATION_STATUS")
    if language is not None:
        field(language, "INVALID_TRANSCRIPT_LANGUAGE", 64)
    provenance, data = source(case, identifier)
    try:
        text = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeError as exc:
        raise ForgeError("INVALID_TRANSCRIPT_ENCODING") from exc
    require("\x00" not in text, "INVALID_TRANSCRIPT_TEXT")
    lines = text.split("\n")
    position, metadata_blocks = 0, 0
    if format_name == "vtt":
        require(bool(re.fullmatch(r"WEBVTT(?:[ \t].*)?", lines[0])) and "-->" not in lines[0],
                "INVALID_WEBVTT_HEADER")
        position = 1
        while position < len(lines) and lines[position].strip():
            require("-->" not in lines[position], "INVALID_WEBVTT_HEADER")
            position += 1
    events = []
    while position < len(lines):
        checkpoint()
        if not lines[position].strip():
            position += 1
            continue
        first = position
        while position < len(lines) and lines[position].strip():
            position += 1
        block = lines[first:position]
        if format_name == "vtt" and (block[0] in ("STYLE", "REGION", "NOTE")
                                     or block[0].startswith(("NOTE ", "NOTE\t"))):
            require("-->" not in "\n".join(block), "INVALID_WEBVTT_METADATA")
            metadata_blocks += 1
            continue
        require(len(events) < MAX_RECORDS, "TOO_MANY_RECORDS")
        cue_id = None
        timing = 0
        if "-->" not in block[0]:
            cue_id, timing = field(block[0], "INVALID_CUE_ID", 200), 1
        if format_name == "srt":
            require(cue_id is not None and bool(re.fullmatch(r"[0-9]+", cue_id)), "INVALID_SRT_INDEX")
        require(len(block) > timing + 1, "INVALID_TRANSCRIPT_CUE")
        match = re.fullmatch(r"(\S+)[ \t]+-->[ \t]+(\S+)(?:[ \t]+(.*))?", block[timing])
        require(match is not None, "INVALID_CUE_TIMING")
        start, end = cue_time(match[1], format_name), cue_time(match[2], format_name)
        require(start < end, "INVALID_CUE_INTERVAL")
        require(format_name == "vtt" or match[3] is None, "UNSUPPORTED_SRT_SETTINGS")
        body = "\n".join(block[timing + 1:])
        field(body, "INVALID_CUE_TEXT")
        require("-->" not in body, "INVALID_CUE_TEXT")
        events.append({"evidence_id": identifier, "record_index": len(events), "cue_id": cue_id,
                       "event": body, "start_ms": start, "end_ms": end,
                       "original_start": match[1], "original_end": match[2],
                       "cue_settings": match[3], "source_line_start": first + 1,
                       "source_line_end": position, "original_timestamp": None,
                       "utc": None, "time_status": "media_relative"})
    require(bool(events), "EMPTY_TRANSCRIPT")
    return result("timed_transcript", provenance, events,
                  ["Cue text and markup are inert source data, not instructions or rendered HTML.",
                   "Times are media-relative cue boundaries, not wall-clock or word-level timestamps.",
                   "Method, language and translation are analyst declarations, not verified properties.",
                   "No transcription, translation, speaker identification or audio verification is performed."],
                  format=format_name, method=method, translation=translation, language=language,
                  metadata_blocks_ignored=metadata_blocks, text_interpretation="verbatim_cue_payload")
