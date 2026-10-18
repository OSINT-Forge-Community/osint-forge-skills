from __future__ import annotations

from collections import Counter
from heapq import nsmallest

from .assurance import check_citations, coverage, dependency_status
from .casefiles import load_case
from .review import records
from .safeio import MAX_JSON, digest, read_bytes, require, safe_path

ACTIONS = {
    "dependency_review": ("of-hypothesis-audit", "Review the revised premise or analysis, then append a corrected claim if warranted."),
    "citation_mismatch": ("of-investigation-report", "Compare the registered locator and quotation with the original; retain any correction as a new claim."),
    "citation_unverifiable": ("of-document-triage", "Inspect the selected range manually or supply a supported derived text with provenance."),
    "citation_missing": ("of-investigation-report", "Add precise locators where available, or retain the citation limitation in the report."),
    "coverage_gap": ("of-hypothesis-audit", "Review the recorded search outcome and scope; collect only if separately authorized, or document the remaining gap."),
    "coverage_undefined": ("of-case-start", "Declare the questions and source categories needed to assess coverage."),
    "evidence_missing": ("of-case-start", "Register explicitly selected evidence before drawing findings."),
    "claims_missing": ("of-investigation-report", "Record evidence-linked observations or explain why the material supports no finding."),
}


def journal_snapshot(root):
    return {name: digest(read_bytes(root / name, MAX_JSON)) if (root / name).exists() else None
            for name in ("case.json", "evidence.jsonl", "claims.jsonl", "review.jsonl")}


def review_queue(case, limit=20):
    require(type(limit) is int and 1 <= limit <= 100, "INVALID_REVIEW_LIMIT")
    before = journal_snapshot(safe_path(case).absolute())
    citations = check_citations(case)
    root, info, evidence, claims = load_case(case)
    ledger = records(root, info)
    statuses = dependency_status(claims, ledger)
    active = {row["id"] for row in claims if statuses[row["id"]]["status"] != "historical"}
    declared = coverage(ledger)
    counts = Counter({kind: 0 for kind in ACTIONS})
    priorities = Counter({str(level): 0 for level in (1, 2, 3)})

    def candidates():
        if not evidence:
            yield 1, "evidence_missing", {}
        for claim in claims:
            identifier = claim["id"]
            if identifier not in active:
                continue
            state = statuses[identifier]
            if state["status"] == "needs_review":
                yield 1, "dependency_review", {"claim_id": identifier, "reason_count": len(state["reasons"])}
            if not claim.get("citations") and (claim["supports"] or claim["contradicts"]):
                yield 3, "citation_missing", {"claim_id": identifier}
        for citation in citations["citations"]:
            if citation["claim_id"] not in active or citation["status"] not in ("mismatch", "unverifiable"):
                continue
            kind = "citation_" + citation["status"]
            yield 1 if citation["status"] == "mismatch" else 2, kind, {
                key: citation[key] for key in ("claim_id", "citation_index", "evidence_id")}
        if evidence and not active:
            yield 2, "claims_missing", {}
        if not declared["requirements"]:
            yield 2, "coverage_undefined", {}
        for question in declared["requirements"]:
            for category in question["categories"]:
                if not category["completed"]:
                    yield 2 if question["priority"] == "critical" else 3, "coverage_gap", {
                        "question_id": question["question_id"], "category": category["category"],
                        "research_ids": category["research_ids"], "recorded_statuses": category["statuses"]}

    def counted():
        for order, (priority, kind, references) in enumerate(candidates()):
            counts[kind] += 1
            priorities[str(priority)] += 1
            yield priority, order, kind, references

    selected = nsmallest(limit, counted(), key=lambda item: item[:2])
    tasks = [{"priority": priority, "kind": kind, "references": references,
              "skill": ACTIONS[kind][0], "next_check": ACTIONS[kind][1]}
             for priority, _, kind, references in selected]
    total = sum(counts.values())
    require(journal_snapshot(root) == before, "CASE_CHANGED_DURING_REVIEW")
    return {"status": "review_items_found" if total else "no_recorded_gaps", "tasks": tasks,
            "total": total, "shown": len(tasks), "omitted": total - len(tasks),
            "counts_by_kind": dict(counts), "counts_by_priority": dict(priorities),
            "current_claims": len(active), "historical_claims": len(claims) - len(active),
            "executed": False, "network_calls": False, "semantic_validation": "not_performed",
            "limits": ["Priorities order recorded review work; they are not confidence, severity or truth scores.",
                       "Only current claims and declared coverage are queued; historical citation checks remain available separately.",
                       "No recorded gap does not establish completeness, authenticity or readiness to publish.",
                       "Suggested checks do not authorize collection, transmission or automatic case changes."]}


def review_summary(case):
    queue = review_queue(case, limit=1)
    return {key: queue[key] for key in ("status", "total", "counts_by_kind", "counts_by_priority",
            "current_claims", "historical_claims", "executed", "network_calls", "semantic_validation", "limits")}
