from __future__ import annotations

import csv
from datetime import datetime
import io
import json
from pathlib import Path
import re

from .safeio import ForgeError, MAX_JSON, MAX_RECORDS, digest, read_bytes, require
from .timestamps import timestamp
from .snapshot import read_operation

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


def validate_review_extensions(root, row, known, evidence, schema, questions=None):
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
        previous = known.get(row.get("supersedes"))
        same_question = questions.get(row.get("question_id")) if questions is not None else next(
            (item for item in known.values() if item["kind"] == kind and item.get("question_id") == row.get("question_id")), None)
        require(isinstance(row.get("question_id"), str) and bool(QUESTION_ID.fullmatch(row["question_id"]))
                and (not same_question or schema >= 4 and previous is not None
                     and previous.get("question_id") == row["question_id"]), "INVALID_QUESTION_ID")
        text(row.get("question"), 4000, "INVALID_REQUIREMENT")
        categories = row.get("source_categories")
        require(isinstance(categories, list) and 0 < len(categories) <= 20, "INVALID_SOURCE_CATEGORIES")
        for category in categories:
            text(category, 100, "INVALID_SOURCE_CATEGORIES")
        require(len(set(categories)) == len(categories), "INVALID_SOURCE_CATEGORIES")
        require(row.get("priority", "supporting") in ("critical", "supporting"), "INVALID_PRIORITY")
    elif kind == "research" and "question_id" in row:
        from .review import current
        requirement = questions.get(row["question_id"]) if questions is not None else next(
            (item for item in current(list(known.values())) if item["kind"] == "requirement" and item["question_id"] == row["question_id"]), None)
        if requirement is not None and requirement.get("retired"):
            requirement = None
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
    positions = {row["id"]: index for index, row in enumerate(rows)}
    indexed = {}
    for search in searches:
        indexed.setdefault((search.get("question_id"), search.get("source_category")), []).append(search)
    requirements = []
    for row in active:
        if row["kind"] != "requirement":
            continue
        categories = []
        for category in row["source_categories"]:
            matches = indexed.get((row["question_id"], category), [])
            stale = {item["id"] for item in matches if row.get("supersedes")
                     and positions[item["id"]] < positions[row["id"]]}
            states = ["needs_review" if item["id"] in stale else item["status"] for item in matches] or ["not_searched"]
            categories.append({"category": category, "statuses": states,
                               "research_ids": [item["id"] for item in matches],
                               "recorded_statuses": [item["status"] for item in matches],
                               "stale_research_ids": sorted(stale),
                               "completed": bool(matches) and all(item == "completed" for item in states)})
        requirements.append({"question_id": row["question_id"], "question": row["question"],
                             "priority": row.get("priority", "supporting"), "categories": categories})
    return {"requirements": requirements,
            "defined_categories": sum(len(row["categories"]) for row in requirements),
            "completed_categories": sum(item["completed"] for row in requirements for item in row["categories"]),
            "limitations": ["Coverage applies only to declared requirements; completed searches do not prove absence.",
                            "Separate searches remain visible; one completed query does not erase another partial query."]}


@read_operation
def case_status(case):
    from .casefiles import load_case, verify
    from .review import records
    verify(case)
    root, info, _, claims = load_case(case)
    rows = records(root, info)
    statuses = dependency_status(claims, rows)
    from .investigation import investigation_status
    return {"claims": list(statuses.values()), "needs_review": sum(row["status"] == "needs_review"
            for row in statuses.values()), "coverage": coverage(rows), "investigation": investigation_status(rows),
            "semantic_validation": "not_performed"}


def selected_excerpt(data, citation, derived, cache=None):
    cache = {} if cache is None else cache
    kind, start, end = (citation[key] for key in ("kind", "start", "end"))
    if kind == "time_ms":
        require(isinstance(derived, dict) and derived.get("analysis_type") == "timed_transcript",
                "CITATION_FORMAT_UNSUPPORTED")
        from .public_imports import transcript_excerpt
        return transcript_excerpt(derived, start, end)
    require(end - start < MAX_RECORDS, "CITATION_RANGE_LIMIT")
    if kind == "page":
        require(isinstance(derived, dict) and derived.get("analysis_type") == "external_tool"
                and derived.get("tool", {}).get("name") == "pdftotext"
                and isinstance(derived.get("result"), str), "CITATION_FORMAT_UNSUPPORTED")
        coverage = derived.get("coverage", {})
        first, last = coverage.get("first_page"), coverage.get("last_page")
        require(type(first) is int and type(last) is int and 1 <= first <= last,
                "CITATION_FORMAT_UNSUPPORTED")
        if "pages" not in cache:
            pages = derived["result"].split("\f")
            if pages and not pages[-1].strip() and derived["result"].endswith("\f"):
                pages.pop()
            require(len(pages) == last - first + 1, "CITATION_PAGE_MAPPING_UNCERTAIN")
            cache["pages"] = pages
        require(first <= start <= end <= last, "CITATION_RANGE_MISMATCH")
        return "\n".join(cache["pages"][start - first:end - first + 1]).replace("\r\n", "\n").replace("\r", "\n")
    if kind == "line":
        if "lines" not in cache:
            if derived is not None:
                value = derived.get("text")
                if value is None and isinstance(derived.get("result"), str):
                    value = derived["result"]
                require(isinstance(value, str), "CITATION_FORMAT_UNSUPPORTED")
            else:
                value = data.decode("utf-8-sig")
            require("\x00" not in value, "CITATION_FORMAT_UNSUPPORTED")
            cache["lines"] = value.splitlines()
        lines = cache["lines"]
        require(end <= len(lines), "CITATION_RANGE_MISMATCH")
        return "\n".join(lines[start - 1:end])
    if derived is not None:
        events = derived.get("events")
        require(isinstance(events, list), "CITATION_FORMAT_UNSUPPORTED")
        require(len(events) <= MAX_RECORDS and all(isinstance(row, dict) for row in events), "CITATION_FORMAT_UNSUPPORTED")
        if "event_index" not in cache:
            indexed = {}
            for row in events:
                index = row.get("record_index")
                if type(index) is int:
                    indexed.setdefault(index, []).append(row)
            cache["event_index"] = indexed
        indexed = cache["event_index"]
        selected = []
        for index in range(start, end + 1):
            require(index in indexed and len(indexed[index]) == 1, "CITATION_RANGE_MISMATCH")
            selected.append(indexed[index][0])
        field = citation.get("field", "event")
    else:
        mode = citation.get("format")
        value = data.decode("utf-8-sig")
        if mode in cache:
            rows = cache[mode]
        elif mode == "csv":
            from .csvio import strict_csv
            _, rows = strict_csv(value, "CITATION_FORMAT_UNSUPPORTED", "CITATION_FORMAT_UNSUPPORTED")
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
        cache[mode] = rows
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


@read_operation
def prepare_citation(case, evidence_id, kind, start, end, analysis=None, format_name=None, field=None):
    from .casefiles import load_case, validate_claim
    from .review import checked_analysis
    root, _, evidence, _ = load_case(case)
    indexed = {row["id"]: row for row in evidence}
    require(evidence_id in indexed, "INVALID_CITATION_REFERENCE")
    citation = {"evidence_id": evidence_id, "kind": kind, "start": start, "end": end}
    derived = None
    if analysis is not None:
        derived, fingerprint = checked_analysis(root, analysis, evidence, evidence_id=evidence_id)
        citation.update(analysis=analysis, sha256=fingerprint)
    if format_name is not None:
        citation["format"] = format_name
    if field is not None:
        citation["field"] = field
    candidate = {"text": "Selected excerpt", "rationale": "Text matching only", "state": "observed",
                 "confidence": "low", "supports": [evidence_id], "contradicts": [], "citations": [citation]}
    validate_claim(candidate, set(indexed))
    data = b"" if derived is not None else read_bytes(root / indexed[evidence_id]["path"], MAX_JSON)
    excerpt = selected_excerpt(data, citation, derived)
    require(0 < len(excerpt) <= 2000 and "\x00" not in excerpt, "CITATION_EXCERPT_LIMIT")
    citation["quote"] = excerpt
    validate_claim(candidate, set(indexed))
    return {"citations": [citation], "excerpt_sha256": digest(excerpt.encode("utf-8")),
            "evidence_sha256": indexed[evidence_id]["sha256"], "status": "prepared",
            "semantic_validation": "not_performed",
            "limitations": ["Review whether the selected excerpt supports every detail of the claim.",
                            "An exact excerpt does not establish truth, authenticity or source independence."]}


def report_review(root, evidence, claims, ledger, citation_checks, analyses=None):
    from .review import checked_analysis
    statuses = dependency_status(claims, ledger)
    active = {row["id"] for row in claims if statuses[row["id"]]["status"] != "historical"}
    missing = [row["id"] for row in claims if row["id"] in active and not row.get("citations")]
    counts = {key: 0 for key in ("mismatch", "unverifiable", "locator_found", "excerpt_found")}
    for row in citation_checks["citations"]:
        if row["claim_id"] in active:
            counts[row["status"]] += 1
    selected = set(analyses or [])
    selected.update(citation["analysis"] for row in claims if row["id"] in active
                    for citation in row.get("citations", []) if "analysis" in citation)
    require(len(selected) <= 100, "TOO_MANY_REVIEW_ANALYSES")
    limits = []
    for path in sorted(selected):
        data, fingerprint = checked_analysis(root, path, evidence)
        if data.get("coverage") in ("partial_export", "supplied_export_only"):
            limits.append({"analysis": path, "sha256": fingerprint, "coverage": data["coverage"],
                           "supplied_records": data.get("supplied_records"),
                           "source_total_count": data.get("source_total_count")})
    declared = coverage(ledger)
    return {"current_claims": len(active), "missing_citations": missing, "citation_counts": counts,
            "coverage_defined": bool(declared["requirements"]),
            "coverage_complete": bool(declared["requirements"]) and
                declared["completed_categories"] == declared["defined_categories"],
            "analysis_limits": limits, "analysis_scope": "current_citations_and_selected_analyses",
            "semantic_validation": "not_performed"}


def review_messages(summary, language):
    fr = language == "fr"
    counts = summary["citation_counts"]
    messages = [
        (f"Conclusions sans citation précise : {len(summary['missing_citations'])}. "
         f"Citations discordantes : {counts['mismatch']}. Invérifiables : {counts['unverifiable']}."
         if fr else f"Claims without precise citations: {len(summary['missing_citations'])}. "
         f"Mismatched citations: {counts['mismatch']}. Unverifiable: {counts['unverifiable']}."),
        (f"Appui aux conclusions à examiner : {summary['current_claims']} conclusions actuelles. "
         "Un extrait exact ne valide pas le raisonnement, les dates ou l'identité."
         if fr else f"Semantic support requires review for {summary['current_claims']} current claims. "
         "An exact excerpt does not validate reasoning, dates or identity.")]
    if not summary["coverage_defined"]:
        messages.append("Couverture non définie : aucune exhaustivité établie." if fr else
                        "Coverage undefined: completeness is not established.")
    elif not summary["coverage_complete"]:
        messages.append("Couverture déclarée incomplète : des recherches restent ouvertes." if fr else
                        "Declared coverage incomplete: research gaps remain.")
    for item in summary["analysis_limits"]:
        label = ("Export partiel" if fr else "Partial export") if item["coverage"] == "partial_export" else (
            "Export fourni uniquement" if fr else "Supplied export only")
        message = f"{label}: {item['analysis']}"
        supplied, total = item["supplied_records"], item["source_total_count"]
        if type(supplied) is int:
            message += f" - {supplied}" + (f" / {total}" if type(total) is int else "")
            message += " notices fournies" if fr else " supplied records"
        messages.append(message)
    return messages


@read_operation
def check_citations(case):
    from .casefiles import load_case, verify
    from .review import checked_analysis
    verify(case)
    root, _, evidence, claims = load_case(case)
    indexed = {row["id"]: row for row in evidence}
    results = []
    sources, analyses, parsed = {}, {}, {}
    cache_bytes = 0
    for claim in claims:
        for index, citation in enumerate(claim.get("citations", [])):
            require(len(results) < MAX_RECORDS, "TOO_MANY_CITATIONS")
            result = {"claim_id": claim["id"], "citation_index": index,
                      "evidence_id": citation["evidence_id"], "semantic_support": "not_checked"}
            try:
                derived = None
                if "analysis" in citation:
                    key = (citation["analysis"], citation["sha256"], citation["evidence_id"])
                    if key not in analyses:
                        value = checked_analysis(root, citation["analysis"], evidence,
                                                 citation["sha256"], citation["evidence_id"])[0]
                        cost = len(json.dumps(value, ensure_ascii=True).encode())
                        if cache_bytes + cost > 4 * MAX_JSON or len(parsed) >= 64:
                            sources.clear()
                            analyses.clear()
                            parsed.clear()
                            cache_bytes = 0
                        analyses[key] = value
                        cache_bytes += cost
                    derived = analyses[key]
                    data = b""
                else:
                    key = citation["evidence_id"]
                    if key not in sources:
                        value = read_bytes(root / indexed[key]["path"], MAX_JSON)
                        if cache_bytes + len(value) > 4 * MAX_JSON or len(parsed) >= 64:
                            sources.clear()
                            analyses.clear()
                            parsed.clear()
                            cache_bytes = 0
                        sources[key] = value
                        cache_bytes += len(value)
                    data = sources[key]
                excerpt = selected_excerpt(data, citation, derived, parsed.setdefault(key, {}))
                quote = citation.get("quote")
                matched = quote is None or quote.replace("\r\n", "\n").replace("\r", "\n") == excerpt
                result.update(status=("excerpt_found" if quote is not None else "locator_found") if matched else "mismatch",
                              excerpt_sha256=digest(excerpt.encode("utf-8")),
                              derivation="derived_not_original" if derived is not None else "registered_bytes")
            except ForgeError as exc:
                code = str(exc)
                if code in ("OPERATION_CANCELLED", "OPERATION_BUDGET_EXCEEDED", "CASE_CHANGED_DURING_READ"):
                    raise
                result.update(status="mismatch" if code in ("CITATION_RANGE_MISMATCH", "CITATION_FIELD_MISMATCH")
                              else "unverifiable", code=code)
            except (UnicodeError, ValueError, csv.Error, RecursionError):
                result.update(status="unverifiable", code="CITATION_FORMAT_UNSUPPORTED")
            results.append(result)
    return {"citations": results, "counts": {status: sum(row["status"] == status for row in results)
            for status in ("excerpt_found", "locator_found", "mismatch", "unverifiable")},
            "normalization": "UTF-8 BOM removed; splitlines and LF joins; exact excerpt comparison; no whitespace folding",
            "semantic_validation": "not_performed"}
