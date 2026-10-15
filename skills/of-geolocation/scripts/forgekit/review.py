from __future__ import annotations

from pathlib import Path
import json
import re

from .safeio import (MAX_JSON, atomic_write, digest, jsonl_bytes, read_bytes,
                     read_json, read_jsonl, relative_path, require)

REVIEW_ID = re.compile(r"R[0-9]{6}\Z")
STATUSES = ("not_searched", "no_result", "partial", "unavailable", "completed")
ENTITY_TYPES = ("organization", "person", "domain", "document", "location", "account", "asset")


def checked_analysis(root, name, evidence, expected=None, evidence_id=None):
    relative_path(name)
    require(len(Path(name).parts) == 2 and Path(name).parts[0] == "analysis",
            "ANALYSIS_INPUT_REQUIRED")
    data = read_bytes(root / name, MAX_JSON)
    require(expected is None or digest(data) == expected, "ANALYSIS_DIGEST_MISMATCH")
    value = json.loads(data, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    require(isinstance(value, dict) and isinstance(value.get("input"), dict),
            "ANALYSIS_PROVENANCE_MISSING")
    source = value["input"]
    indexed = {row["id"]: row for row in evidence}
    identifier = source.get("evidence_id")
    require(isinstance(identifier, str) and identifier in indexed
            and source.get("sha256") == indexed[identifier]["sha256"]
            and (evidence_id is None or identifier == evidence_id), "ANALYSIS_PROVENANCE_MISMATCH")
    return value, digest(data)


def validate_review(root, evidence, claims, rows, schema=2):
    from .casefiles import bounded_text
    known, replaced = {}, set()
    evidence_ids = {row["id"] for row in evidence}
    for row in rows:
        identifier = row.get("id")
        require(isinstance(identifier, str) and bool(REVIEW_ID.fullmatch(identifier))
                and identifier not in known, "INVALID_REVIEW_ID")
        kind = row.get("kind")
        require(kind in ("research", "entity", "relation", "annotation", "requirement", "analysis_revision"), "INVALID_REVIEW_KIND")
        bounded_text(row.get("recorded_at"), 100, "INVALID_REVIEW_TIME")
        bounded_text(row.get("rationale"), 8000, "INVALID_REVIEW_RATIONALE")
        references = row.get("evidence", [])
        require(isinstance(references, list) and len(references) <= 100
                and all(isinstance(ref, str) and ref in evidence_ids for ref in references)
                and len(set(references)) == len(references), "INVALID_EVIDENCE_REFERENCE")
        previous = row.get("supersedes")
        if previous is not None:
            require(kind in ("research", "annotation") and isinstance(previous, str)
                    and previous in known and known[previous]["kind"] == kind
                    and previous not in replaced, "INVALID_REVIEW_REVISION")
            replaced.add(previous)
        allowed = {"id", "kind", "recorded_at", "rationale", "evidence", "supersedes"}
        if kind == "research":
            allowed |= {"question", "query", "scope", "tool", "status"}
            for key in ("question", "scope", "query", "tool"):
                bounded_text(row.get(key), 4000, "INVALID_RESEARCH_FIELD")
            require(row.get("status") in STATUSES, "INVALID_RESEARCH_STATUS")
        elif kind == "entity":
            allowed |= {"entity_type", "label"}
            require(row.get("entity_type") in ENTITY_TYPES and bool(references), "INVALID_ENTITY")
            bounded_text(row.get("label"), 300, "INVALID_ENTITY_LABEL")
        elif kind == "relation":
            allowed |= {"source", "target", "label", "state"}
            for key in ("source", "target"):
                ref = row.get(key)
                require(isinstance(ref, str) and ref in known and known[ref]["kind"] == "entity",
                        "INVALID_ENTITY_REFERENCE")
            require(row["source"] != row["target"] and bool(references), "INVALID_RELATION")
            require(row.get("state") in ("observed", "candidate"), "INVALID_RELATION_STATE")
            bounded_text(row.get("label"), 300, "INVALID_RELATION_LABEL")
        elif kind == "annotation":
            allowed |= {"analysis", "sha256", "record_index", "tags", "note"}
            require(isinstance(row.get("sha256"), str) and bool(re.fullmatch(r"[0-9a-f]{64}", row["sha256"])),
                    "INVALID_DIGEST")
            data, _ = checked_analysis(root, row.get("analysis"), evidence, row["sha256"])
            index = row.get("record_index")
            events = data.get("events")
            require(type(index) is int and index >= 0 and isinstance(events, list)
                    and any(isinstance(event, dict) and type(event.get("record_index")) is int
                            and event.get("record_index") == index
                            and event.get("evidence_id") == data["input"]["evidence_id"] for event in events),
                    "INVALID_EVENT_REFERENCE")
            tags = row.get("tags")
            require(isinstance(tags, list) and len(tags) <= 20
                    and all(isinstance(tag, str) and bool(re.fullmatch(r"[a-zA-Z0-9_-]{1,40}", tag))
                            for tag in tags), "INVALID_TAGS")
            bounded_text(row.get("note"), 4000, "INVALID_ANNOTATION")
        from .assurance import validate_review_extensions
        validate_review_extensions(root, row, known, evidence, schema)
        if schema >= 3:
            extra_by_kind = {"research": {"question_id", "source_category"},
                "entity": {"identifiers", "jurisdiction", "candidate_group"},
                "relation": {"match_criteria"}, "annotation": set(),
                "requirement": {"question_id", "question", "source_categories", "priority"},
                "analysis_revision": {"previous_analysis", "previous_sha256", "replacement_analysis", "replacement_sha256"}}
            allowed |= extra_by_kind[kind] | {"time_context"}
        require(set(row) <= allowed, "UNKNOWN_REVIEW_FIELD")
        known[identifier] = row


def records(root, info):
    return read_jsonl(root / "review.jsonl") if info["schema_version"] >= 2 else []


def current(rows):
    replaced = {row.get("supersedes") for row in rows}
    return [row for row in rows if row["id"] not in replaced]


def append_review(case, record):
    from .casefiles import case_lock, load_case, utc_now, verify
    require(isinstance(record, dict) and not {"id", "recorded_at"} & record.keys(), "INVALID_REVIEW_INPUT")
    verify(case)
    root, info, _, _ = load_case(case)
    require(info["schema_version"] >= 2, "CASE_UPGRADE_REQUIRED")
    with case_lock(root):
        _, info, evidence, claims = load_case(root)
        rows = records(root, info)
        identifier = f"R{max((int(row['id'][1:]) for row in rows), default=0) + 1:06d}"
        entry = {**record, "id": identifier, "recorded_at": utc_now()}
        validate_review(root, evidence, claims, rows + [entry], info["schema_version"])
        atomic_write(root / "review.jsonl", jsonl_bytes(rows + [entry]), replace=True)
    return {"id": identifier, "kind": entry["kind"]}


def intake_manifest(case, manifest):
    from .casefiles import add_many
    data = read_json(manifest)
    require(isinstance(data, dict) and set(data) == {"files"} and isinstance(data["files"], list),
            "INVALID_INTAKE_MANIFEST")
    paths, metadata = [], []
    for item in data["files"]:
        require(isinstance(item, dict) and set(item) <= {"path", "source_url", "origin_group"}
                and isinstance(item.get("path"), str), "INVALID_INTAKE_MANIFEST")
        relative_path(item["path"])
        paths.append(Path(manifest).absolute().parent / item["path"])
        metadata.append({key: value for key, value in item.items() if key != "path"})
    return add_many(case, paths, metadata=metadata)
