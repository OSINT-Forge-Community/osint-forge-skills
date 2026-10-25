from __future__ import annotations

from .safeio import checkpoint, require

KINDS = ("hypothesis", "test", "origin")
FIELDS = {
    "hypothesis": {"label", "statement", "status", "prediction", "alternatives", "question_id"},
    "test": {"hypothesis", "action", "expected", "status", "observation", "outcome"},
    "origin": {"claim_id", "citation_index", "origin_group", "relationship", "basis"},
}


def validate_investigation(row, known, evidence_ids, claims, schema):
    from .casefiles import bounded_text
    kind = row["kind"]
    require(schema >= 4 or kind not in KINDS and "retired" not in row, "CASE_UPGRADE_REQUIRED")
    if "retired" in row:
        require(type(row["retired"]) is bool and row.get("supersedes") is not None, "INVALID_REVIEW_RETIREMENT")
    if kind == "hypothesis":
        bounded_text(row.get("label"), 300, "INVALID_HYPOTHESIS")
        bounded_text(row.get("statement"), 4000, "INVALID_HYPOTHESIS")
        require(row.get("status") in ("candidate", "supported", "rejected", "unresolved"), "INVALID_HYPOTHESIS_STATUS")
        if "prediction" in row:
            bounded_text(row["prediction"], 4000, "INVALID_HYPOTHESIS_PREDICTION")
        alternatives = row.get("alternatives", [])
        require(isinstance(alternatives, list) and len(alternatives) <= 20
                and all(isinstance(item, str) and item in known and known[item]["kind"] == "hypothesis"
                        for item in alternatives) and len(set(alternatives)) == len(alternatives), "INVALID_HYPOTHESIS_ALTERNATIVE")
        if "question_id" in row:
            require(any(item["kind"] == "requirement" and item.get("question_id") == row["question_id"]
                        for item in known.values()), "INVALID_REQUIREMENT_REFERENCE")
        require(row["status"] not in ("supported", "rejected") or bool(row.get("evidence")), "HYPOTHESIS_WITHOUT_EVIDENCE")
    elif kind == "test":
        parent = row.get("hypothesis")
        require(isinstance(parent, str) and parent in known and known[parent]["kind"] == "hypothesis", "INVALID_HYPOTHESIS_REFERENCE")
        bounded_text(row.get("action"), 4000, "INVALID_TEST_ACTION")
        bounded_text(row.get("expected"), 4000, "INVALID_TEST_EXPECTATION")
        require(row.get("status") in ("planned", "blocked", "completed", "inconclusive"), "INVALID_TEST_STATUS")
        require(row.get("outcome", "undetermined") in ("supports", "contradicts", "undetermined"), "INVALID_TEST_OUTCOME")
        if "observation" in row:
            bounded_text(row["observation"], 4000, "INVALID_TEST_OBSERVATION")
        require(row["status"] != "completed" or bool(row.get("evidence")) and bool(row.get("observation")), "TEST_WITHOUT_OBSERVATION")
        require(row["status"] in ("completed", "inconclusive") or row.get("outcome", "undetermined") == "undetermined", "UNOBSERVED_TEST_OUTCOME")
    elif kind == "origin":
        indexed = {claim["id"]: claim for claim in claims}
        claim = row.get("claim_id")
        require(isinstance(claim, str) and claim in indexed, "INVALID_ORIGIN_CLAIM")
        index = row.get("citation_index")
        require(type(index) is int and 0 <= index < len(indexed[claim].get("citations", [])), "INVALID_ORIGIN_CITATION")
        bounded_text(row.get("origin_group"), 100, "INVALID_ORIGIN_GROUP")
        bounded_text(row.get("basis"), 4000, "INVALID_ORIGIN_BASIS")
        require(row.get("relationship") in ("copied", "direct_observation", "unknown"), "INVALID_ORIGIN_RELATIONSHIP")
        require(bool(row.get("evidence")) and set(row["evidence"]) <= evidence_ids, "INVALID_EVIDENCE_REFERENCE")
    return FIELDS.get(kind, set())


def investigation_status(rows):
    from .review import current
    active = current(rows)
    hypotheses = [row for row in active if row["kind"] == "hypothesis"]
    tests = [row for row in active if row["kind"] == "test"]
    origins = [row for row in active if row["kind"] == "origin"]
    replaced = {row["supersedes"]: row for row in rows if row.get("supersedes")}
    test_rows = []
    for test in tests:
        checkpoint()
        parent = test["hypothesis"]
        stale = parent in replaced
        while parent in replaced:
            checkpoint()
            parent = replaced[parent]["id"]
        test_rows.append({**test, "needs_review": stale, "current_hypothesis": parent})
    return {"hypotheses": hypotheses, "tests": test_rows, "origins": origins,
            "open_hypotheses": sum(row["status"] in ("candidate", "unresolved") for row in hypotheses),
            "open_tests": sum(row["status"] in ("planned", "blocked", "inconclusive") or row["needs_review"] for row in test_rows),
            "source_independence": "not_inferred", "semantic_validation": "not_performed"}
