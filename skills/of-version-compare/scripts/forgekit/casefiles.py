from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from . import SCHEMA_VERSION, VERSION
from .safeio import (ForgeError, MAX_RECORDS, MAX_TOTAL, atomic_write, digest, json_bytes,
                     jsonl_bytes, read_bytes, read_json, read_jsonl, relative_path,
                     require, safe_path, checkpoint)

EVIDENCE_ID = re.compile(r"E[0-9]{6}\Z")
CLAIM_ID = re.compile(r"C[0-9]{6}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def bounded_text(value: object, maximum: int, code: str) -> str:
    require(isinstance(value, str) and 0 < len(value) <= maximum, code)
    require("\x00" not in value, code)
    return value


@contextmanager
def case_lock(root: Path):
    path = safe_path(root / ".forge.lock", exists=False)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ForgeError("CASE_BUSY") from exc
    try:
        os.close(descriptor)
        yield
    finally:
        path.unlink(missing_ok=True)


def initialize(path: str | Path, title: str, scope: str) -> dict:
    bounded_text(title, 300, "INVALID_TITLE")
    bounded_text(scope, 8000, "INVALID_SCOPE")
    root = safe_path(path, exists=False)
    require(not root.exists(), "CASE_EXISTS")
    safe_path(root.parent)
    root.mkdir(mode=0o700)
    for name in ("raw", "analysis", "reports", "exports"):
        (root / name).mkdir(mode=0o700)
    case = {"schema_version": SCHEMA_VERSION, "tool_version": VERSION,
            "title": title, "scope": scope, "created_at": utc_now(),
            "acquisition_authenticity": "not_established",
            "model_trials": []}
    atomic_write(root / "case.json", json_bytes(case))
    atomic_write(root / "evidence.jsonl", b"")
    atomic_write(root / "claims.jsonl", b"")
    atomic_write(root / "review.jsonl", b"")
    return {"status": "created", "schema_version": SCHEMA_VERSION}


def load_case(path: str | Path) -> tuple[Path, dict, list[dict], list[dict]]:
    from .snapshot import active_case
    cached = active_case(path)
    if cached is not None:
        return cached
    root = safe_path(path)
    require(root.is_dir(), "DIRECTORY_REQUIRED")
    for folder in ("raw", "analysis", "reports", "exports"):
        require(safe_path(root / folder).is_dir(), "INVALID_CASE_DIRECTORY")
    case = read_json(root / "case.json")
    require(isinstance(case, dict) and type(case.get("schema_version")) is int
            and case["schema_version"] in (1, 2, 3, SCHEMA_VERSION),
            "UNSUPPORTED_CASE_SCHEMA")
    bounded_text(case.get("title"), 300, "INVALID_TITLE")
    bounded_text(case.get("scope"), 8000, "INVALID_SCOPE")
    evidence = read_jsonl(root / "evidence.jsonl")
    claims = read_jsonl(root / "claims.jsonl")
    ids = set()
    total = 0
    for row in evidence:
        checkpoint()
        identifier = row.get("id")
        require(isinstance(identifier, str) and bool(EVIDENCE_ID.fullmatch(identifier))
                and identifier not in ids, "INVALID_EVIDENCE_ID")
        ids.add(identifier)
        require(row.get("path") == f"raw/{identifier}.bin", "INVALID_EVIDENCE_PATH")
        relative_path(row["path"])
        require(isinstance(row.get("sha256"), str)
                and bool(SHA256.fullmatch(row["sha256"])), "INVALID_DIGEST")
        require(type(row.get("size")) is int and row["size"] >= 0, "INVALID_SIZE")
        total += row["size"]
        bounded_text(row.get("original_name"), 255, "INVALID_SOURCE_NAME")
        bounded_text(row.get("collected_at"), 100, "INVALID_COLLECTION_TIME")
        group = row.get("origin_group")
        require(group is None or isinstance(group, str) and 0 < len(group) <= 100,
                "INVALID_ORIGIN_GROUP")
        validate_url(row.get("source_url"))
    require(total <= MAX_TOTAL, "CASE_TOO_LARGE")
    claim_ids, replaced = set(), set()
    for row in claims:
        checkpoint()
        identifier = row.get("id")
        require(isinstance(identifier, str) and bool(CLAIM_ID.fullmatch(identifier))
                and identifier not in claim_ids, "INVALID_CLAIM_ID")
        validate_claim(row, ids)
        previous = row.get("supersedes")
        require(previous is None or isinstance(previous, str) and previous in claim_ids,
                "INVALID_CLAIM_REVISION")
        require(previous is None or previous not in replaced, "CLAIM_ALREADY_REVISED")
        if previous is not None:
            replaced.add(previous)
        require(case["schema_version"] >= 2 or not (row.get("citations") or previous),
                "CASE_UPGRADE_REQUIRED")
        from .assurance import validate_claim_extensions
        validate_claim_extensions(row, claim_ids, case["schema_version"])
        claim_ids.add(identifier)
    if case["schema_version"] >= 2:
        from .review import validate_review
        validate_review(root, evidence, claims, read_jsonl(root / "review.jsonl"), case["schema_version"])
    else:
        require(not (root / "review.jsonl").exists(), "CASE_UPGRADE_REQUIRED")
    return root, case, evidence, claims


def validate_url(value: object) -> str | None:
    if value is None:
        return None
    bounded_text(value, 2000, "INVALID_SOURCE_URL")
    try:
        url = urlsplit(value)
        require(url.scheme == "https" and bool(url.hostname) and not url.username
                and not url.password and not url.query and not url.fragment
                and not any(c.isspace() or not c.isprintable() for c in value),
                "INVALID_SOURCE_URL")
        _ = url.port
    except ValueError as exc:
        raise ForgeError("INVALID_SOURCE_URL") from exc
    return value


def validate_claim(row: dict, evidence_ids: set[str]) -> None:
    bounded_text(row.get("text"), 4000, "INVALID_CLAIM_TEXT")
    bounded_text(row.get("rationale"), 8000, "INVALID_CLAIM_RATIONALE")
    require(row.get("state") in ("observed", "inferred", "unconfirmed"),
            "INVALID_CLAIM_STATE")
    require(row.get("confidence") in ("low", "medium", "high"),
            "INVALID_CONFIDENCE")
    for key in ("supports", "contradicts"):
        references = row.get(key)
        require(isinstance(references, list) and len(references) <= 100
                and all(isinstance(ref, str) and ref in evidence_ids for ref in references)
                and len(references) == len(set(references)), "INVALID_EVIDENCE_REFERENCE")
    require(not set(row["supports"]) & set(row["contradicts"]), "OVERLAPPING_REFERENCES")
    require(row["state"] == "unconfirmed" or bool(row["supports"]),
            "FACT_WITHOUT_EVIDENCE")
    require(row["state"] != "unconfirmed" or row["confidence"] == "low",
            "UNCONFIRMED_CONFIDENCE")
    require(not row["contradicts"] or row["confidence"] != "high",
            "UNRESOLVED_CONTRADICTION")
    citations = row.get("citations", [])
    require(isinstance(citations, list) and len(citations) <= 100, "INVALID_CITATIONS")
    for citation in citations:
        require(isinstance(citation, dict)
                and set(citation) <= {"evidence_id", "kind", "start", "end", "quote", "analysis", "sha256", "format", "field"}
                and citation.get("evidence_id") in row["supports"] + row["contradicts"],
                "INVALID_CITATION_REFERENCE")
        require(citation.get("kind") in ("page", "line", "record", "time_ms"), "INVALID_CITATION_KIND")
        lower = 1 if citation["kind"] in ("page", "line") else 0
        require(type(citation.get("start")) is int and type(citation.get("end")) is int
                and lower <= citation["start"] <= citation["end"] <= 10**12, "INVALID_CITATION_RANGE")
        if "quote" in citation:
            bounded_text(citation["quote"], 2000, "INVALID_CITATION_QUOTE")
        if "format" in citation:
            require(citation["format"] in ("text", "csv", "json", "jsonl"), "INVALID_CITATION_FORMAT")
        if "field" in citation:
            bounded_text(citation["field"], 200, "INVALID_CITATION_FIELD")
            require(citation["kind"] == "record", "INVALID_CITATION_FIELD")
        if "analysis" in citation:
            relative_path(citation["analysis"])
            require(Path(citation["analysis"]).parts[0] == "analysis"
                    and len(Path(citation["analysis"]).parts) == 2
                    and isinstance(citation.get("sha256"), str)
                    and bool(SHA256.fullmatch(citation["sha256"])), "INVALID_CITATION_ANALYSIS")
        else:
            require("sha256" not in citation, "INVALID_CITATION_ANALYSIS")


def verify(path: str | Path) -> dict:
    from .snapshot import active_case
    cached = active_case(path)
    if cached is not None:
        require(not (cached[0] / ".forge.lock").exists(), "CASE_BUSY")
        return {"status": "verified", "evidence_count": len(cached[2]), "claim_count": len(cached[3]),
                "scope": "registered_bytes_and_references", "authenticity": "not_established",
                "semantic_claim_validation": "not_performed"}
    root, _, evidence, claims = load_case(path)
    require(not (root / ".forge.lock").exists(), "CASE_BUSY")
    return _verify_records(root, evidence, claims)


def _verify_records(root: Path, evidence: list[dict], claims: list[dict]) -> dict:
    indexed = {row["path"] for row in evidence}
    actual = set()
    for entry in (root / "raw").iterdir():
        safe_path(entry)
        require(entry.is_file(), "UNEXPECTED_RAW_ENTRY")
        actual.add(entry.relative_to(root).as_posix())
    require(actual == indexed, "RAW_INVENTORY_MISMATCH")
    for row in evidence:
        checkpoint()
        content = read_bytes(root / row["path"])
        require(len(content) == row["size"] and digest(content) == row["sha256"],
                "EVIDENCE_INTEGRITY_MISMATCH")
    for row in claims:
        for citation in row.get("citations", []):
            if "analysis" in citation:
                from .review import checked_analysis
                checked_analysis(root, citation["analysis"], evidence,
                                 citation["sha256"], citation["evidence_id"])
    return {"status": "verified", "evidence_count": len(evidence),
            "claim_count": len(claims), "scope": "registered_bytes_and_references",
            "authenticity": "not_established", "semantic_claim_validation": "not_performed"}


def add_evidence(path: str | Path, source: str | Path, *, source_url: str | None = None,
                 origin_group: str | None = None) -> dict:
    source = safe_path(source)
    validate_url(source_url)
    if origin_group is not None:
        bounded_text(origin_group, 100, "INVALID_ORIGIN_GROUP")
    content = read_bytes(source)
    if content.startswith(b"SQLite format 3\x00"):
        require(not Path(str(source) + "-wal").exists(), "SQLITE_WAL_PRESENT")
    verify(path)
    root, _, evidence, _ = load_case(path)
    require(not source.is_relative_to(root), "SOURCE_MUST_BE_OUTSIDE_CASE")
    require(sum(row["size"] for row in evidence) + len(content) <= MAX_TOTAL,
            "CASE_TOO_LARGE")
    bounded_text(source.name, 255, "INVALID_SOURCE_NAME")
    with case_lock(root):
        _, _, evidence, _ = load_case(root)
        require(sum(row["size"] for row in evidence) + len(content) <= MAX_TOTAL,
                "CASE_TOO_LARGE")
        identifier = f"E{max((int(row['id'][1:]) for row in evidence), default=0) + 1:06d}"
        require(bool(EVIDENCE_ID.fullmatch(identifier)), "EVIDENCE_LIMIT_REACHED")
        row = {"id": identifier, "path": f"raw/{identifier}.bin", "sha256": digest(content),
               "size": len(content), "original_name": source.name,
               "collected_at": utc_now(), "source_url": source_url,
               "origin_group": origin_group, "origin_independence": "unverified"}
        journal = jsonl_bytes(evidence + [row])
        atomic_write(root / row["path"], content)
        atomic_write(root / "evidence.jsonl", journal, replace=True)
    return {"id": identifier, "sha256": row["sha256"], "size": row["size"]}


def add_many(path: str | Path, sources: list[str | Path], *, source_url: str | None = None,
             origin_group: str | None = None, metadata: list[dict] | None = None) -> dict:
    require(isinstance(sources, list) and 0 < len(sources) <= MAX_RECORDS, "INVALID_BATCH_SIZE")
    validate_url(source_url)
    if origin_group is not None:
        bounded_text(origin_group, 100, "INVALID_ORIGIN_GROUP")
    root, _, _, _ = load_case(path)
    selected = [safe_path(source) for source in sources]
    if metadata is None:
        metadata = [{"source_url": source_url, "origin_group": origin_group} for _ in selected]
    require(isinstance(metadata, list) and len(metadata) == len(selected), "INVALID_INTAKE_MANIFEST")
    for item in metadata:
        require(isinstance(item, dict) and set(item) <= {"source_url", "origin_group"}, "INVALID_INTAKE_MANIFEST")
        validate_url(item.get("source_url"))
        if item.get("origin_group") is not None:
            bounded_text(item["origin_group"], 100, "INVALID_ORIGIN_GROUP")
    require(all(not source.is_relative_to(root) for source in selected), "SOURCE_MUST_BE_OUTSIDE_CASE")
    added = []
    with case_lock(root):
        _, _, evidence, claims = load_case(root)
        _verify_records(root, evidence, claims)
        require(len(evidence) + len(selected) <= MAX_RECORDS, "TOO_MANY_RECORDS")
        total = sum(row["size"] for row in evidence)
        next_id = max((int(row["id"][1:]) for row in evidence), default=0) + 1
        for source, item in zip(selected, metadata):
            content = read_bytes(source)
            if content.startswith(b"SQLite format 3\x00"):
                require(not Path(str(source) + "-wal").exists(), "SQLITE_WAL_PRESENT")
            bounded_text(source.name, 255, "INVALID_SOURCE_NAME")
            require(total + len(content) <= MAX_TOTAL, "CASE_TOO_LARGE")
            identifier = f"E{next_id:06d}"
            require(bool(EVIDENCE_ID.fullmatch(identifier)), "EVIDENCE_LIMIT_REACHED")
            row = {"id": identifier, "path": f"raw/{identifier}.bin", "sha256": digest(content),
                   "size": len(content), "original_name": source.name,
                   "collected_at": utc_now(), "source_url": item.get("source_url"),
                   "origin_group": item.get("origin_group"), "origin_independence": "unverified"}
            journal = jsonl_bytes(evidence + [row])
            atomic_write(root / row["path"], content)
            atomic_write(root / "evidence.jsonl", journal, replace=True)
            evidence.append(row)
            added.append({"id": identifier, "sha256": row["sha256"], "size": row["size"]})
            total += len(content)
            next_id += 1
            del content
        _, _, evidence, claims = load_case(root)
        _verify_records(root, evidence, claims)
    return {"status": "added", "evidence_count": len(added), "evidence": added}


def add_claim(path: str | Path, text: str, supports: list[str], contradicts: list[str],
              state: str, confidence: str, rationale: str, *, citations: list[dict] | None = None,
              supersedes: str | None = None, depends_on: list[str] | None = None,
              time_context: dict | None = None) -> dict:
    require(citations is None or isinstance(citations, list), "INVALID_CITATIONS")
    verify(path)
    root, _, _, _ = load_case(path)
    with case_lock(root):
        _, info, evidence, claims = load_case(root)
        identifier = f"C{max((int(row['id'][1:]) for row in claims), default=0) + 1:06d}"
        require(bool(CLAIM_ID.fullmatch(identifier)), "CLAIM_LIMIT_REACHED")
        row = {"id": identifier, "text": text, "supports": supports,
               "contradicts": contradicts, "state": state,
               "confidence": confidence, "rationale": rationale}
        if depends_on is not None:
            row["depends_on"] = depends_on
        if time_context is not None:
            row["time_context"] = time_context
        if citations or supersedes:
            require(info["schema_version"] >= 2, "CASE_UPGRADE_REQUIRED")
        if citations:
            row["citations"] = citations
        if supersedes is not None:
            require(supersedes in {c["id"] for c in claims}, "INVALID_CLAIM_REVISION")
            require(not any(c.get("supersedes") == supersedes for c in claims), "CLAIM_ALREADY_REVISED")
            row["supersedes"] = supersedes
        if info["schema_version"] >= 2:
            row["recorded_at"] = utc_now()
        validate_claim(row, {entry["id"] for entry in evidence})
        from .assurance import validate_claim_extensions
        validate_claim_extensions(row, {entry["id"] for entry in claims}, info["schema_version"])
        for citation in row.get("citations", []):
            if "analysis" in citation:
                from .review import checked_analysis
                checked_analysis(root, citation["analysis"], evidence,
                                 citation["sha256"], citation["evidence_id"])
        atomic_write(root / "claims.jsonl", jsonl_bytes(claims + [row]), replace=True)
    return {"id": identifier, "state": state}


def evidence_bytes(path: str | Path, identifier: str) -> tuple[dict, bytes]:
    verify(path)
    root, _, evidence, _ = load_case(path)
    row = next((entry for entry in evidence if entry["id"] == identifier), None)
    require(row is not None, "EVIDENCE_NOT_FOUND")
    return row, read_bytes(root / row["path"])


def provenance(path: str | Path) -> dict:
    verify(path)
    _, _, evidence, _ = load_case(path)
    parent = {row["id"]: row["id"] for row in evidence}

    def find(value):
        while parent[value] != value:
            value = parent[value]
        return value

    by_digest, by_origin = {}, {}
    for row in evidence:
        identifier = row["id"]
        for key, index in ((row["sha256"], by_digest), (row["origin_group"], by_origin)):
            if key is None:
                continue
            if key in index:
                parent[find(identifier)] = find(index[key])
            else:
                index[key] = identifier
    groups = {}
    for row in evidence:
        groups.setdefault(find(row["id"]), []).append(row["id"])
    return {"evidence_count": len(evidence), "candidate_origin_groups": list(groups.values()),
            "independence_between_groups": "unknown",
            "grouping_basis": ["identical_bytes", "analyst_supplied_origin_labels"],
            "limitations": ["Different domains or different hashes do not establish independence.",
                            "Origin labels require evidence-backed analyst review."]}
