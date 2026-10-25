from __future__ import annotations

import csv
import difflib
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from .casefiles import evidence_bytes, load_case, verify
from .review import checked_analysis, current, records
from .safeio import ForgeError, MAX_JSON, MAX_RECORDS, digest, read_json, require, visible
from .timestamps import timestamp
from .assurance import dependency_status
from .snapshot import read_operation


def source(case, identifier):
    row, data = evidence_bytes(case, identifier)
    require(len(data) <= MAX_JSON, "STRUCTURED_INPUT_TOO_LARGE")
    return {"evidence_id": row["id"], "sha256": row["sha256"]}, data


def import_events(case, identifier, time_field, event_field):
    provenance, data = source(case, identifier)
    require(time_field != event_field, "INVALID_EVENT_MAPPING")
    try:
        from .csvio import strict_csv
        headers, rows = strict_csv(data.decode("utf-8-sig"), "INVALID_EVENT_MAPPING")
    except (csv.Error, UnicodeError) as exc:
        raise ForgeError("INVALID_CSV_INPUT") from exc
    require(headers is not None and len(headers) == len(set(headers))
            and time_field in headers and event_field in headers, "INVALID_EVENT_MAPPING")
    events = []
    for index, row in enumerate(rows):
        require(index < MAX_RECORDS, "TOO_MANY_EVENTS")
        require(None not in row and all(value is not None for value in row.values()), "INVALID_CSV_ROW")
        event = row[event_field]
        require(0 < len(event) <= 4000, "INVALID_EVENT_TEXT")
        moment = timestamp(row[time_field])
        events.append({"evidence_id": identifier, "record_index": index, "event": event,
                       "original_timestamp": row[time_field], "utc": moment["utc"],
                       "time_status": moment["time_status"]})
    events.sort(key=lambda row: (row["utc"] is None,
                                datetime.fromisoformat(row["utc"]) if row["utc"] else datetime.max.replace(tzinfo=timezone.utc)))
    return {"analysis_type": "mapped_csv", "input": provenance, "events": events,
            "event_count": len(events), "mapping": {"timestamp": time_field, "event": event_field},
            "unmapped_columns": [key for key in headers if key not in (time_field, event_field)],
            "limitations": ["Only selected CSV columns are interpreted. Original rows remain in the evidence.",
                            "Exporter identity, artifact semantics and clock accuracy require analyst review."]}


def timesketch_csv(case, analysis):
    verify(case)
    root, _, evidence, _ = load_case(case)
    data, analysis_digest = checked_analysis(root, analysis, evidence)
    events = data.get("events")
    require(isinstance(events, list) and len(events) <= MAX_RECORDS, "EVENT_ANALYSIS_REQUIRED")
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["datetime", "message", "timestamp_desc", "evidence_id", "record_index", "analysis_sha256"])
    omitted = 0
    for event in events:
        require(isinstance(event, dict) and event.get("evidence_id") == data["input"]["evidence_id"]
                and type(event.get("record_index")) is int and event["record_index"] >= 0,
                "INVALID_EVENT_REFERENCE")
        moment = timestamp(event.get("utc"))
        if moment["utc"] is None:
            omitted += 1
            continue
        message = visible(event.get("event", event.get("title", "")), 4000)
        if message.lstrip().startswith(("=", "+", "-", "@")):
            message = "'" + message
        writer.writerow([moment["utc"], message, "Imported recorded event time; clock unverified",
                         event["evidence_id"], event.get("record_index"), analysis_digest])
    return output.getvalue().encode(), {"exported_events": len(events) - omitted,
            "omitted_uncertain_events": omitted, "analysis_sha256": analysis_digest,
            "losses": ["Unknown times omitted; no timezone invented.",
                       "Other event fields and annotations are not exported; leading formula characters are neutralized."],
            "target": "Timesketch CSV documented fields; live import not established"}


class CaptureText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "template"):
            self.hidden += 1
        if tag in ("p", "div", "br", "li", "h1", "h2", "h3"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "template"):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def capture(case, identifier, format_name):
    provenance, data = source(case, identifier)
    locations = []
    if format_name == "mhtml":
        message = BytesParser(policy=policy.default).parsebytes(data)
        parts = list(message.walk())
        require(len(parts) <= 100, "TOO_MANY_CAPTURE_PARTS")
        html_parts = [part for part in parts if part.get_content_type() == "text/html"
                      and part.get_content_disposition() != "attachment"]
        require(len(html_parts) == 1, "AMBIGUOUS_CAPTURE_DOCUMENT")
        selected = html_parts[0]
        payload = selected.get_payload(decode=True)
        require(isinstance(payload, bytes) and len(payload) <= MAX_JSON, "CAPTURE_TOO_LARGE")
        try:
            text = payload.decode(selected.get_content_charset() or "utf-8")
        except (LookupError, UnicodeError) as exc:
            raise ForgeError("INVALID_CAPTURE_ENCODING") from exc
        locations = [str(part["Content-Location"])[:2000] for part in (message, selected)
                     if part["Content-Location"]]
    else:
        require(format_name == "html", "UNSUPPORTED_CAPTURE_FORMAT")
        text = data.decode("utf-8-sig")
    parser = CaptureText()
    parser.feed(text)
    parser.close()
    return {"analysis_type": "web_capture", "input": provenance,
            "text": "".join(parser.parts), "declared_locations": locations,
            "format": format_name, "network_calls": False,
            "limitations": ["Text extraction is not browser rendering; CSS visibility and dynamic content are not reconstructed.",
                            "Embedded locations are untrusted declarations, not authenticated acquisition URLs.",
                            "Scripts, attachments and linked resources are not executed or fetched."]}


@read_operation
def compare_text(case, left=None, right=None, left_analysis=None, right_analysis=None,
                 left_sha256=None, right_sha256=None):
    root, _, evidence, _ = load_case(case)

    def selected(identifier, analysis, fingerprint):
        require((identifier is None) != (analysis is None), "INVALID_COMPARISON_SELECTOR")
        if analysis is None:
            require(fingerprint is None, "INVALID_COMPARISON_SELECTOR")
            return source(case, identifier)
        require(isinstance(fingerprint, str) and bool(re.fullmatch(r"[0-9a-f]{64}", fingerprint)),
                "ANALYSIS_DIGEST_REQUIRED")
        value, actual = checked_analysis(root, analysis, evidence, fingerprint)
        text = value.get("text", value.get("result"))
        require(isinstance(text, str), "TEXT_ANALYSIS_REQUIRED")
        return {**value["input"], "analysis": analysis, "analysis_sha256": actual,
                "derivation": "derived_not_independent_source", "tool": value.get("tool"),
                "coverage": value.get("coverage", {})}, text.encode("utf-8")

    first, a = selected(left, left_analysis, left_sha256)
    second, b = selected(right, right_analysis, right_sha256)
    require(first != second and len(a) <= 200000 and len(b) <= 200000, "TEXT_DIFF_LIMIT")
    a_lines, b_lines = a.decode("utf-8-sig").splitlines(), b.decode("utf-8-sig").splitlines()
    require(len(a_lines) <= 1000 and len(b_lines) <= 1000, "TEXT_DIFF_LIMIT")
    changes = []
    for kind, i, j, k, m in difflib.SequenceMatcher(None, a_lines, b_lines, autojunk=False).get_opcodes():
        if kind != "equal":
            changes.append({"kind": kind, "left_lines": [i + 1, j], "right_lines": [k + 1, m],
                            "removed": a_lines[i:j], "added": b_lines[k:m]})
    return {"analysis_type": "text_comparison", "inputs": [first, second],
            "changes": changes, "identical_bytes": a == b,
            "limitations": ["Left and right are operator-selected versions, not proven publication order.",
                            "Empty ranges mark insertions/deletions. BOM and line-ending changes are not text changes."]}


@read_operation
def graph(case):
    verify(case)
    root, info, evidence, claims = load_case(case)
    ledger = records(root, info)
    rows = current(ledger)
    nodes = [{"id": row["id"], "kind": "evidence", "label": row["original_name"]} for row in evidence]
    statuses = dependency_status(claims, rows)
    nodes += [{"id": row["id"], "kind": "claim", "label": row["text"],
               "review_status": statuses[row["id"]]["status"], "time_context": row.get("time_context", {})} for row in claims]
    active = {row["id"] for row in rows}
    replacements = {row["supersedes"]: row["id"] for row in ledger if row.get("supersedes")}
    entities = {row["id"]: row for row in ledger if row["kind"] == "entity"}

    def endpoint(identifier):
        while identifier in replacements:
            identifier = replacements[identifier]
        return identifier

    nodes += [{"id": row["id"], "kind": row["entity_type"], "label": row["label"],
               "review_status": "retired" if row.get("retired") else "current" if row["id"] in active else "historical",
               **{key: row[key] for key in ("identifiers", "jurisdiction", "candidate_group", "time_context") if key in row}}
              for row in entities.values()]
    edges = []
    for row in claims:
        for key in ("supports", "contradicts"):
            edges += [{"source": ref, "target": row["id"], "label": key,
                       "state": "analyst_asserted", "evidence": [ref]} for ref in row[key]]
        for parent in row.get("depends_on", []):
            edges.append({"source": parent, "target": row["id"], "label": "premise",
                          "state": statuses[row["id"]]["status"], "evidence": row["supports"]})
        if row.get("supersedes"):
            edges.append({"source": row["id"], "target": row["supersedes"], "label": "supersedes",
                          "state": "recorded", "evidence": row["supports"]})
    for row in rows:
        if row["kind"] == "entity":
            edges += [{"source": ref, "target": row["id"], "label": "documents",
                       "state": "analyst_asserted", "evidence": [ref]} for ref in row["evidence"]]
        if row["kind"] == "relation":
            edge = {key: row[key] for key in ("source", "target", "label", "state", "evidence", "time_context", "match_criteria") if key in row}
            edge.update(source=endpoint(row["source"]), target=endpoint(row["target"]))
            if entities[edge["source"]].get("retired") or entities[edge["target"]].get("retired"):
                edge["state"] = "needs_review"
            edges.append(edge)
    return {"nodes": nodes, "edges": edges,
            "limitations": ["Relations are analyst assertions or candidates, not automatic identity resolution."]}


def graphml(case):
    data = graph(case)
    root = ET.Element("graphml", xmlns="http://graphml.graphdrawing.org/xmlns")
    for key in ("kind", "label", "state", "evidence", "review_status", "time_context", "identifiers", "jurisdiction", "candidate_group", "match_criteria"):
        ET.SubElement(root, "key", {"id": key, "for": "all", "attr.name": key, "attr.type": "string"})
    container = ET.SubElement(root, "graph", id="case", edgedefault="directed")
    for node in data["nodes"]:
        element = ET.SubElement(container, "node", id=node["id"])
        for key in ("kind", "label", "review_status", "time_context", "identifiers", "jurisdiction", "candidate_group"):
            if key in node:
                value = node[key]
                ET.SubElement(element, "data", key=key).text = visible(
                    json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else value, MAX_JSON)
    for index, edge in enumerate(data["edges"]):
        element = ET.SubElement(container, "edge", id=f"edge{index}", source=edge["source"], target=edge["target"])
        for key in ("label", "state", "evidence", "time_context", "match_criteria"):
            if key in edge:
                value = edge[key]
                ET.SubElement(element, "data", key=key).text = visible(
                    json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else value, MAX_JSON)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
