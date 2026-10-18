from __future__ import annotations

import csv
from datetime import datetime
import io
import json
from pathlib import Path
import re

from .safeio import ForgeError, MAX_JSON, MAX_RECORDS, digest, read_bytes, require
from .timestamps import timestamp

QUESTION_ID = re.compile(r"Q[1-9][0-9]{0,5}\Z")
TIME_FIELDS = {"event_time", "published_at", "available_at", "valid_from", "valid_until"}


def text(value, limit, code):
    require(isinstance(value, str) and 0 < len(value) <= limit and "\x00" not in value, code)


def time_context(value):
    require(isinstance(value, dict) and set(value) <= TIME_FIELDS and bool(value), "INVALID_TIME_CONTEXT")
    for item in value.values():
        text(item, 100, "INVALID_TIME_CONTEXT")
        require(timestamp(item)["time_status"] != "invalid", "INVALID_TIME_CONTEXT")
    lower, upper = (timestamp(value.get(key)) for key in ("valid_from", "valid_until"))
    if lower["utc"] and upper["utc"]:
        require(datetime.fromisoformat(lower["utc"]) <= datetime.fromisoformat(upper["utc"]),
                "INVALID_VALIDITY_INTERVAL")


def validate_claim_extensions(row, earlier, schema):
    fields = {"depends_on", "time_context"} & row.keys()
    extended_citations = any({"format", "field"} & item.keys() for item in row.get("citations", []))
    require(schema >= 3 or not (fields or extended_citations), "CASE_UPGRADE_REQUIRED")
    dependencies = row.get("depends_on", [])
    require(isinstance(dependencies, list) and len(dependencies) <= 100
            and all(isinstance(item, str) and item in earlier for item in dependencies)
            and len(set(dependencies)) == len(dependencies), "INVALID_CLAIM_DEPENDENCY")
    if "time_context" in row:
        time_context(row["time_context"])


def validate_review_extensions(root, row, known, evidence, schema):
    from .review import checked_analysis
    extra = {"time_context", "question_id", "source_category", "identifiers", "jurisdiction",
             "candidate_group", "match_criteria", "priority", "source_categories",
             "previous_analysis", "previous_sha256", "replacement_analysis", "replacement_sha256"}
    kind = row["kind"]
    require(schema >= 3 or not (extra & row.keys() or kind in ("requirement", "analysis_revision")),
            "CASE_UPGRADE_REQUIRED")
    if "time_context" in row:
        time_context(row["time_context"])
    if kind == "requirement":
        require(isinstance(row.get("question_id"), str) and bool(QUESTION_ID.fullmatch(row["question_id"]))
                and not any(item.get("question_id") == row["question_id"] and item["kind"] == kind
                            for item in known.values()), "INVALID_QUESTION_ID")
        text(row.get("question"), 4000, "INVALID_REQUIREMENT")
        categories = row.get("source_categories")
        require(isinstance(categories, list) and 0 < len(categories) <= 20, "INVALID_SOURCE_CATEGORIES")
        for category in categories:
            text(category, 100, "INVALID_SOURCE_CATEGORIES")
        require(len(set(categories)) == len(categories), "INVALID_SOURCE_CATEGORIES")
        require(row.get("priority", "supporting") in ("critical", "supporting"), "INVALID_PRIORITY")
    elif kind == "research" and "question_id" in row:
        requirement = next((item for item in known.values() if item["kind"] == "requirement"
                            and item["question_id"] == row["question_id"]), None)
        require(requirement is not None and row.get("source_category") in requirement["source_categories"],
                "INVALID_REQUIREMENT_REFERENCE")
    elif kind == "research":
        require("source_category" not in row, "INVALID_REQUIREMENT_REFERENCE")
    if kind == "entity":
        if "jurisdiction" in row:
            text(row["jurisdiction"], 100, "INVALID_JURISDICTION")
        if "candidate_group" in row:
            text(row["candidate_group"], 100, "INVALID_CANDIDATE_GROUP")
        if "identifiers" in row:
            require(isinstance(row["identifiers"], list) and len(row["identifiers"]) <= 20, "INVALID_IDENTIFIERS")
            for item in row["identifiers"]:
                require(isinstance(item, dict) and set(item) == {"scheme", "value"}, "INVALID_IDENTIFIERS")
                text(item["scheme"], 100, "INVALID_IDENTIFIERS")
                text(item["value"], 300, "INVALID_IDENTIFIERS")
    if kind == "relation" and "match_criteria" in row:
        text(row["match_criteria"], 4000, "INVALID_MATCH_CRITERIA")
    if kind == "analysis_revision":
        previous = row.get("previous_analysis"), row.get("previous_sha256")
        replacement = row.get("replacement_analysis"), row.get("replacement_sha256")
        for name, fingerprint in (previous, replacement):
            require(isinstance(fingerprint, str) and bool(re.fullmatch(r"[0-9a-f]{64}", fingerprint)),
                    "INVALID_DIGEST")
            checked_analysis(root, name, evidence, fingerprint)
        require(previous[0] != replacement[0], "INVALID_ANALYSIS_REVISION")
        a, _ = checked_analysis(root, previous[0], evidence, previous[1])
        b, _ = checked_analysis(root, replacement[0], evidence, replacement[1])
        require(a["input"] == b["input"], "ANALYSIS_PROVENANCE_MISMATCH")
        retired = {item["previous_analysis"]: item["replacement_analysis"]
                   for item in known.values() if item["kind"] == "analysis_revision"}
        require(previous[0] not in retired, "ANALYSIS_ALREADY_REVISED")
        cursor, visited = replacement[0], {previous[0]}
        while cursor in retired:
            require(cursor not in visited, "ANALYSIS_REVISION_CYCLE")
            visited.add(cursor)
            cursor = retired[cursor]
        require(cursor not in visited, "ANALYSIS_REVISION_CYCLE")
    return extra


def dependency_status(claims, rows):
    replaced = {row["supersedes"]: row["id"] for row in claims if row.get("supersedes")}
    retired = {(row["previous_analysis"], row["previous_sha256"]): row["id"]
               for row in rows if row["kind"] == "analysis_revision"}
    result = {}
    for row in claims:
        reasons = []
        for parent in row.get("depends_on", []):
            if parent in replaced:
                reasons.append({"kind": "claim_revised", "path": [row["id"], parent],
                                "replacement": replaced[parent]})
            for reason in result[parent]["reasons"]:
                require(len(reason["path"]) < MAX_RECORDS, "DEPENDENCY_DEPTH_LIMIT")
                reasons.append({**reason, "path": [row["id"], *reason["path"]]})
                require(len(reasons) <= 1000, "DEPENDENCY_PATH_LIMIT")
        for citation in row.get("citations", []):
            key = citation.get("analysis"), citation.get("sha256")
            if key in retired:
                reasons.append({"kind": "analysis_revised", "path": [row["id"]],
                                "analysis": key[0], "revision": retired[key]})
        result[row["id"]] = {"id": row["id"], "status": "historical" if row["id"] in replaced
                              else "needs_review" if reasons else "current",
                              "depends_on": row.get("depends_on", []), "reasons": reasons}
    return result


def coverage(rows):
    from .review import current
    active = current(rows)
    searches = [row for row in active if row["kind"] == "research"]
    requirements = []
    for row in active:
        if row["kind"] != "requirement":
            continue
        categories = []
        for category in row["source_categories"]:
            matches = [item for item in searches if item.get("question_id") == row["question_id"]
                       and item.get("source_category") == category]
            states = [item["status"] for item in matches] or ["not_searched"]
            categories.append({"category": category, "statuses": states,
                               "research_ids": [item["id"] for item in matches],
                               "completed": bool(matches) and all(item == "completed" for item in states)})
        requirements.append({"question_id": row["question_id"], "question": row["question"],
                             "priority": row.get("priority", "supporting"), "categories": categories})
    return {"requirements": requirements,
            "defined_categories": sum(len(row["categories"]) for row in requirements),
            "completed_categories": sum(item["completed"] for row in requirements for item in row["categories"]),
            "limitations": ["Coverage applies only to declared requirements; completed searches do not prove absence.",
                            "Separate searches remain visible; one completed query does not erase another partial query."]}


def case_status(case):
    from .casefiles import load_case, verify
    from .review import records
    verify(case)
    root, info, _, claims = load_case(case)
    rows = records(root, info)
    statuses = dependency_status(claims, rows)
    return {"claims": list(statuses.values()), "needs_review": sum(row["status"] == "needs_review"
            for row in statuses.values()), "coverage": coverage(rows), "semantic_validation": "not_performed"}


def selected_excerpt(data, citation, derived):
    kind, start, end = (citation[key] for key in ("kind", "start", "end"))
    require(end - start < MAX_RECORDS, "CITATION_RANGE_LIMIT")
    if kind in ("page", "time_ms"):
        raise ForgeError("CITATION_FORMAT_UNSUPPORTED")
    if kind == "line":
        if derived is not None:
            value = derived.get("text")
            if value is None and isinstance(derived.get("result"), str):
                value = derived["result"]
            require(isinstance(value, str), "CITATION_FORMAT_UNSUPPORTED")
        else:
            value = data.decode("utf-8-sig")
        require("\x00" not in value, "CITATION_FORMAT_UNSUPPORTED")
        lines = value.splitlines()
        require(end <= len(lines), "CITATION_RANGE_MISMATCH")
        return "\n".join(lines[start - 1:end])
    if derived is not None:
        events = derived.get("events")
        require(isinstance(events, list), "CITATION_FORMAT_UNSUPPORTED")
        require(len(events) <= MAX_RECORDS and all(isinstance(row, dict) for row in events), "CITATION_FORMAT_UNSUPPORTED")
        indexed = {}
        for row in events:
            index = row.get("record_index")
            if type(index) is int and start <= index <= end:
                require(index not in indexed, "CITATION_RANGE_MISMATCH")
                indexed[index] = row
        selected = []
        for index in range(start, end + 1):
            require(index in indexed, "CITATION_RANGE_MISMATCH")
            selected.append(indexed[index])
        field = citation.get("field", "event")
    else:
        mode = citation.get("format")
        value = data.decode("utf-8-sig")
        if mode == "csv":
            reader = csv.DictReader(io.StringIO(value, newline=""), strict=True)
            headers = reader.fieldnames
            require(headers is not None and len(headers) == len(set(headers)), "CITATION_FORMAT_UNSUPPORTED")
            rows = []
            for row in reader:
                require(len(rows) < MAX_RECORDS and None not in row
                        and all(item is not None for item in row.values()), "CITATION_FORMAT_UNSUPPORTED")
                rows.append(row)
        elif mode in ("json", "jsonl"):
            reject = lambda _: (_ for _ in ()).throw(ValueError())
            if mode == "json":
                rows = json.loads(value, parse_constant=reject)
            else:
                rows = []
                for line in io.StringIO(value):
                    require(len(rows) < MAX_RECORDS, "CITATION_FORMAT_UNSUPPORTED")
                    rows.append(json.loads(line, parse_constant=reject))
            require(isinstance(rows, list) and len(rows) <= MAX_RECORDS, "CITATION_FORMAT_UNSUPPORTED")
        else:
            raise ForgeError("CITATION_FORMAT_UNSUPPORTED")
        require(end < len(rows), "CITATION_RANGE_MISMATCH")
        selected = rows[start:end + 1]
        field = citation.get("field")
    pieces = []
    for row in selected:
        if field:
            require(isinstance(row, dict) and field in row, "CITATION_FIELD_MISMATCH")
            row = row[field]
        pieces.append(row if isinstance(row, str) else json.dumps(row, ensure_ascii=False, sort_keys=True))
    return "\n".join(pieces)


def check_citations(case):
    from .casefiles import load_case, verify
    from .review import checked_analysis
    verify(case)
    root, _, evidence, claims = load_case(case)
    indexed = {row["id"]: row for row in evidence}
    results = []
    for claim in claims:
        for index, citation in enumerate(claim.get("citations", [])):
            require(len(results) < MAX_RECORDS, "TOO_MANY_CITATIONS")
            result = {"claim_id": claim["id"], "citation_index": index,
                      "evidence_id": citation["evidence_id"], "semantic_support": "not_checked"}
            try:
                derived = None
                if "analysis" in citation:
                    derived, _ = checked_analysis(root, citation["analysis"], evidence,
                                                   citation["sha256"], citation["evidence_id"])
                    data = b""
                else:
                    data = read_bytes(root / indexed[citation["evidence_id"]]["path"], MAX_JSON)
                excerpt = selected_excerpt(data, citation, derived)
                quote = citation.get("quote")
                matched = quote is None or quote.replace("\r\n", "\n").replace("\r", "\n") == excerpt
                result.update(status=("excerpt_found" if quote is not None else "locator_found") if matched else "mismatch",
                              excerpt_sha256=digest(excerpt.encode("utf-8")),
                              derivation="derived_not_original" if derived is not None else "registered_bytes")
            except ForgeError as exc:
                code = str(exc)
                result.update(status="mismatch" if code in ("CITATION_RANGE_MISMATCH", "CITATION_FIELD_MISMATCH")
                              else "unverifiable", code=code)
            except (UnicodeError, ValueError, csv.Error, RecursionError):
                result.update(status="unverifiable", code="CITATION_FORMAT_UNSUPPORTED")
            results.append(result)
    return {"citations": results, "counts": {status: sum(row["status"] == status for row in results)
            for status in ("excerpt_found", "locator_found", "mismatch", "unverifiable")},
            "normalization": "UTF-8 BOM removed; splitlines and LF joins; exact excerpt comparison; no whitespace folding",
            "semantic_validation": "not_performed"}
