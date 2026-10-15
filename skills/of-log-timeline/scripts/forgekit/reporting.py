from __future__ import annotations

import io
from pathlib import Path
import re
import zipfile

from . import SCHEMA_VERSION, VERSION
from .casefiles import load_case, provenance, verify
from .safeio import (ForgeError, MAX_FILE, MAX_JSON, MAX_TOTAL, atomic_write, digest,
                     json_bytes, markdown, read_bytes, relative_path, require,
                     safe_path, visible)
from .safeio import zip_directory_guard
from .review import current, records
from .assurance import check_citations, coverage, dependency_status
import json
import os
import tempfile

SECRET = re.compile(r"(?i)(?:bearer\s+|(?:api(?:\\?[_-])?key|password|secret|token)\s*[:=]\s*)(?=\S)")
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
PRIVATE_KEY = re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")
ACTIVE_HTML = re.compile(r"<!doctype\s+html\b|<html(?:\s|>)|<script(?:\s|>)", re.I)


def mask_credentials(text: str) -> tuple[str, int]:
    parts, offset, count = [], 0, 0
    while match := SECRET.search(text, offset):
        end = match.end()
        bearer = text[match.start():match.start() + 6].lower() == "bearer"
        while end < len(text) and not text[end].isspace():
            if not bearer and text[end] in ",;":
                break
            entity = next((value for value in ("&amp;", "&lt;", "&gt;")
                           if text.startswith(value, end)), None) if text[end] == "&" else None
            end += len(entity) if entity else 1
        parts.extend((text[offset:match.start()], "[REDACTED]"))
        offset = end
        count += 1
    parts.append(text[offset:])
    return "".join(parts), count


def render_report(case: str | Path, language: str = "en") -> bytes:
    verify(case)
    _, info, evidence, claims = load_case(case)
    root, _, _, _ = load_case(case)
    review = records(root, info)
    statuses = dependency_status(claims, review)
    citation_checks = check_citations(case)
    require(language in ("en", "fr"), "UNSUPPORTED_LANGUAGE")
    labels = ({"title": "Rapport d'enquête", "scope": "Périmètre", "claims": "Conclusions",
               "support": "Pièces favorables", "against": "Pièces contradictoires",
               "why": "Justification et limites", "evidence": "Inventaire des pièces",
               "limits": "Limites de vérification", "state": "État", "confidence": "Confiance",
               "collected": "acquisition", "bytes": "octets", "groups": "Groupes d'origine candidats",
               "independence": "Indépendance entre les groupes : inconnue.", "generated": "Produit avec"}
              if language == "fr" else
              {"title": "Investigation report", "scope": "Scope", "claims": "Claims",
               "support": "Supporting evidence", "against": "Contradicting evidence",
               "why": "Rationale and limitations", "evidence": "Evidence inventory",
               "limits": "Verification limitations", "state": "State", "confidence": "Confidence",
               "collected": "collected", "bytes": "bytes", "groups": "Candidate origin groups",
               "independence": "Independence between groups: unknown.", "generated": "Generated with"})
    lines = [f"# {labels['title']}: {markdown(info['title'])}", "",
             f"## {labels['scope']}", "", markdown(info["scope"], 8000), "",
             f"## {labels['claims']}", ""]
    for claim in claims:
        citations = lambda key: ", ".join(f"[{ref}](../raw/{ref}.bin)" for ref in claim[key]) or "-"
        lines.extend([f"### {claim['id']}: {markdown(claim['text'])}", "",
                      f"{labels['state']}: `{claim['state']}` | {labels['confidence']}: `{claim['confidence']}`", "",
                      f"{labels['support']}: {citations('supports')}", "",
                      f"{labels['against']}: {citations('contradicts')}", "",
                      f"{labels['why']}: {markdown(claim['rationale'], 8000)}", ""])
        status = statuses[claim["id"]]
        if status["status"] == "needs_review":
            label = "À réexaminer" if language == "fr" else "Needs review"
            lines.extend([f"**{label}**: " + markdown(json.dumps(status["reasons"], ensure_ascii=False), MAX_JSON), ""])
        if claim.get("depends_on"):
            lines.extend([("Dépend de" if language == "fr" else "Depends on") + ": " + ", ".join(claim["depends_on"]), ""])
        if claim.get("time_context"):
            lines.extend([markdown(json.dumps(claim["time_context"], ensure_ascii=False)), ""])
        if claim.get("supersedes"):
            lines.extend([f"Supersedes: {claim['supersedes']}", ""])
        successors = [row["id"] for row in claims if row.get("supersedes") == claim["id"]]
        if successors:
            lines.extend([f"Historical / Historique: replaced by {', '.join(successors)}", ""])
        for citation in claim.get("citations", []):
            lines.append(f"- {citation['evidence_id']} {citation['kind']} "
                         f"{citation['start']}–{citation['end']}: {markdown(citation.get('quote', ''))}"
                         + (f" ({markdown(citation['analysis'])}; SHA-256 {citation['sha256']})"
                            if 'analysis' in citation else ""))
    if review:
        lines.extend(["", "## Recherches et annotations" if language == "fr" else "## Research and annotations", ""])
        for row in current(review):
            lines.append(f"- {row['id']} [{row['kind']} / {row.get('status', row.get('state', 'recorded'))}] "
                         f"{markdown(row.get('question', row.get('label', row.get('note', ''))))}: "
                         f"{markdown(row['rationale'], 8000)}")
    lines.extend(["", "## Couverture déclarée" if language == "fr" else "## Declared coverage", "",
                  markdown(json.dumps(coverage(review), ensure_ascii=False), MAX_JSON), "",
                  "## Contrôle des citations" if language == "fr" else "## Citation checks", "",
                  markdown(json.dumps(citation_checks, ensure_ascii=False), MAX_JSON), "",
                  f"## {labels['evidence']}", ""])
    for row in evidence:
        lines.append(f"- [{row['id']}](../{row['path']}): {markdown(row['original_name'])}; "
                     f"SHA-256 `{row['sha256']}`; {row['size']} {labels['bytes']}; "
                     f"{labels['collected']} {markdown(row['collected_at'])}.")
    lines.extend(["", f"## {labels['limits']}", ""])
    if language == "fr":
        lines.extend(["Les empreintes contrôlent les octets enregistrés. Elles ne prouvent ni l'authenticité, ni la date d'origine, ni une chaîne de conservation judiciaire.", "",
                      "Les références des conclusions sont contrôlées structurellement. Leur pertinence et l'indépendance des sources demandent une vérification humaine."])
    else:
        lines.extend(["Hashes verify registered bytes. They do not establish authenticity, original dates, or a legal chain of custody.", "",
                      "Claim references are checked structurally. Their relevance and source independence require analyst review."])
    groups = provenance(case)
    lines.extend(["", labels['groups'] + ": " + "; ".join(
        ", ".join(group) for group in groups["candidate_origin_groups"]), "",
        labels['independence'], "",
        f"{labels['generated']} OSINT Forge Skills {VERSION}.", ""])
    data = "\n".join(lines).encode("utf-8")
    require(len(data) <= MAX_JSON, "REPORT_TOO_LARGE")
    return data


def prepare_share(source: str | Path, output: str | Path) -> dict:
    destination = safe_path(output, exists=False)
    require("raw" not in destination.parts, "RAW_OUTPUT_REJECTED")
    original = read_bytes(source, MAX_JSON)
    text = visible(original.decode("utf-8"), MAX_JSON)
    require(not ACTIVE_HTML.search(text), "HTML_PUBLIC_VIEW_REJECTED")
    require(not PRIVATE_KEY.search(text), "PRIVATE_KEY_INPUT_REJECTED")
    counts = {}
    text, counts["credentials"] = mask_credentials(text)
    for name, pattern in (("email", EMAIL), ("ipv4", IPV4)):
        text, counts[name] = pattern.subn("[REDACTED]", text)
    text = re.sub(r"\[([^\]]+)\]\(\.\./raw/[^)]+\)", r"\1", text)
    text = re.sub(r"\b[0-9a-f]{64}\b", "[PRIVATE-DIGEST-REMOVED]", text)
    data = text.encode("utf-8")
    atomic_write(destination, data)
    return {"status": "review_required", "sha256": digest(data), "automatic_masks": counts,
            "limitations": ["Names, locations, identifiers and sensitive context may remain.",
                            "No public export is approved by this heuristic masking step."]}


def zip_bytes(members: dict[str, bytes]) -> bytes:
    require(len(members) < 1024, "EXPORT_TOO_MANY_ENTRIES")
    require(sum(len(data) for data in members.values()) <= MAX_TOTAL, "EXPORT_TOO_LARGE")
    manifest = {"schema_version": 1, "tool_version": VERSION,
                "integrity_scope": "member_bytes_since_export_not_authenticity",
                "files": [{"path": name, "sha256": digest(data), "size": len(data)}
                          for name, data in sorted(members.items())]}
    members = {**members, "export-manifest.json": json_bytes(manifest)}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100600 << 16
            archive.writestr(info, data)
    return buffer.getvalue()


def export_case(case: str | Path, output: str | Path, mode: str,
                view: str | Path | None = None, approved_sha256: str | None = None) -> dict:
    verify(case)
    root, _, evidence, _ = load_case(case)
    destination = safe_path(output, exists=False)
    require(not destination.is_relative_to(root / "raw"), "RAW_OUTPUT_REJECTED")
    if mode == "public":
        require(view is not None and approved_sha256 is not None, "EXACT_VIEW_APPROVAL_REQUIRED")
        data = read_bytes(view, MAX_JSON)
        require(digest(data) == approved_sha256, "APPROVAL_DIGEST_MISMATCH")
        text = data.decode("utf-8")
        require(not ACTIVE_HTML.search(text), "HTML_PUBLIC_VIEW_REJECTED")
        require(not (SECRET.search(text) or PRIVATE_KEY.search(text) or EMAIL.search(text)
                     or IPV4.search(text)), "PUBLIC_VIEW_REQUIRES_REDACTION")
        require(visible(text, MAX_JSON) == text, "PUBLIC_VIEW_HAS_CONTROLS")
        require("../raw/" not in text, "PUBLIC_VIEW_HAS_PRIVATE_LINKS")
        members = {"report.md": data, "sharing.json": json_bytes({
            "mode": "public", "view_sha256": approved_sha256,
            "approval": "operator_supplied_digest_not_independently_authenticated",
            "review_scope": "operator_responsibility"})}
    else:
        require(mode == "private", "INVALID_EXPORT_MODE")
        require(view is None and approved_sha256 is None, "INVALID_PRIVATE_EXPORT_OPTIONS")
        members = {name: read_bytes(root / name, MAX_JSON)
                   for name in ("case.json", "evidence.jsonl", "claims.jsonl")}
        if load_case(root)[1]["schema_version"] >= 2:
            members["review.jsonl"] = read_bytes(root / "review.jsonl", MAX_JSON)
        for row in evidence:
            members[row["path"]] = read_bytes(root / row["path"])
        for folder in ("analysis", "reports"):
            for entry in sorted((root / folder).iterdir()):
                safe_path(entry)
                require(entry.is_file(), "UNEXPECTED_DERIVED_ENTRY")
                members[entry.relative_to(root).as_posix()] = read_bytes(entry, MAX_JSON)
        members["sharing.json"] = json_bytes({"mode": "private", "contains_originals": True})
    data = zip_bytes(members)
    verify(root)
    atomic_write(destination, data)
    return {"mode": mode, "sha256": digest(data), "member_count": len(members) + 1}


def inspect_export(path: str | Path) -> dict[str, bytes]:
    data = read_bytes(path, MAX_TOTAL + 1024 * 1024)
    zip_directory_guard(data, 1024)
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            require(len(entries) <= 1024, "EXPORT_TOO_MANY_ENTRIES")
            names = [entry.filename for entry in entries]
            require(len(names) == len(set(names)), "DUPLICATE_ARCHIVE_MEMBER")
            require("export-manifest.json" in names, "EXPORT_MANIFEST_MISSING")
            require(sum(entry.file_size for entry in entries) <= MAX_TOTAL + MAX_JSON,
                    "EXPORT_TOO_LARGE")
            for entry in entries:
                relative_path(entry.filename)
                require(not entry.is_dir() and entry.file_size <= MAX_FILE,
                        "UNSAFE_ARCHIVE_MEMBER")
                require(entry.compress_type == zipfile.ZIP_STORED, "UNSUPPORTED_EXPORT_COMPRESSION")
                mode = entry.external_attr >> 16
                require(not mode or mode & 0o170000 in (0, 0o100000), "UNSAFE_ARCHIVE_MEMBER")
            info = archive.getinfo("export-manifest.json")
            require(info.file_size <= MAX_JSON, "EXPORT_MANIFEST_TOO_LARGE")
            manifest = json.loads(archive.read(info))
            require(isinstance(manifest, dict) and type(manifest.get("schema_version")) is int
                    and manifest["schema_version"] == 1,
                    "UNSUPPORTED_EXPORT_SCHEMA")
            records = manifest.get("files")
            require(isinstance(records, list) and len(records) == len(names) - 1,
                    "INVALID_EXPORT_MANIFEST")
            require(all(isinstance(row, dict) and isinstance(row.get("path"), str)
                        for row in records), "INVALID_EXPORT_MANIFEST")
            indexed = {row["path"] for row in records}
            require(len(indexed) == len(records) and indexed == set(names) - {"export-manifest.json"},
                    "EXPORT_INVENTORY_MISMATCH")
            members = {}
            for row in records:
                content = archive.read(row["path"])
                require(type(row.get("size")) is int and len(content) == row["size"]
                        and digest(content) == row.get("sha256"), "EXPORT_INTEGRITY_MISMATCH")
                members[row["path"]] = content
            return members
    except (zipfile.BadZipFile, ValueError, UnicodeError, KeyError, RuntimeError,
            NotImplementedError, RecursionError) as exc:
        raise ForgeError("INVALID_EXPORT_ARCHIVE") from exc


def verify_export(path: str | Path) -> dict:
    members = inspect_export(path)
    return {"status": "verified", "member_count": len(members),
            "scope": "export_member_bytes", "authenticity": "not_established"}


def restore_case(path: str | Path, destination: str | Path) -> dict:
    members = inspect_export(path)
    try:
        sharing = json.loads(members.get("sharing.json", b"{}"))
    except (ValueError, UnicodeError) as exc:
        raise ForgeError("INVALID_SHARING_METADATA") from exc
    require(isinstance(sharing, dict) and sharing.get("mode") == "private",
            "PRIVATE_CASE_EXPORT_REQUIRED")
    required = {"case.json", "evidence.jsonl", "claims.jsonl", "sharing.json"}
    require(required <= members.keys(), "CASE_RECORDS_MISSING")
    for name in members:
        parts = Path(name).parts
        require(name in required or name == "review.jsonl"
                or len(parts) == 2 and parts[0] in ("raw", "analysis", "reports"),
                "UNEXPECTED_CASE_MEMBER")
    output = safe_path(destination, exists=False)
    require(not output.exists(), "OUTPUT_EXISTS")
    safe_path(output.parent)
    with tempfile.TemporaryDirectory(prefix=".forge-restore-", dir=output.parent) as temporary:
        root = Path(temporary) / "case"
        root.mkdir(mode=0o700)
        for name in ("raw", "analysis", "reports", "exports"):
            (root / name).mkdir(mode=0o700)
        for name, content in members.items():
            if name != "sharing.json":
                atomic_write(root / name, content)
        checked = verify(root)
        safe_path(output, exists=False)
        require(not output.exists(), "OUTPUT_EXISTS")
        os.rename(root, output)
    return {"status": "restored", "evidence_count": checked["evidence_count"],
            "authenticity": "not_established"}


def upgrade_case(case, destination):
    root, info, _, _ = load_case(case)
    require(info["schema_version"] < SCHEMA_VERSION, "CASE_ALREADY_CURRENT")
    output = safe_path(destination, exists=False)
    require(not output.exists() and not output.is_relative_to(root), "INVALID_UPGRADE_DESTINATION")
    with tempfile.TemporaryDirectory(prefix=".forge-upgrade-", dir=safe_path(output.parent)) as temporary:
        archive = Path(temporary) / "original.zip"
        converted = Path(temporary) / "case"
        export_case(root, archive, "private")
        restore_case(archive, converted)
        metadata = json.loads(read_bytes(converted / "case.json", MAX_JSON))
        metadata["schema_version"] = SCHEMA_VERSION
        metadata["upgraded_from"] = {"schema_version": info["schema_version"], "export_sha256": digest(read_bytes(archive, MAX_TOTAL + MAX_JSON))}
        atomic_write(converted / "case.json", json_bytes(metadata), replace=True)
        if info["schema_version"] == 1:
            atomic_write(converted / "review.jsonl", b"")
        verify(converted)
        require(not output.exists(), "OUTPUT_EXISTS")
        os.rename(converted, output)
    return {"status": "upgraded_copy", "schema_version": SCHEMA_VERSION, "original_unchanged": True}
