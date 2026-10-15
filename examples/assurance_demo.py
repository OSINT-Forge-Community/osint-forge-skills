from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(ROOT / "skills/of-case-start/scripts"))
from forgekit.agents import agent_events
from forgekit.analysis import save_analysis
from forgekit.assurance import case_status, check_citations
from forgekit.casefiles import add_claim, add_many, initialize, verify
from forgekit.exchange import graphml, import_events, timesketch_csv
from forgekit.planning import plan
from forgekit.reporting import export_case, render_report, restore_case
from forgekit.review import append_review
from forgekit.safeio import atomic_write, digest, json_bytes, read_bytes, require, safe_path
from forgekit.viewer import render_html


def demo(destination):
    output = safe_path(destination, exists=False)
    require(not output.exists(), "OUTPUT_EXISTS")
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    output.mkdir(mode=0o700)
    inputs = output / "inputs"
    inputs.mkdir(mode=0o700)
    (inputs / "plan.txt").write_text("Harbor Example Ltd\nOpening planned for 09:00; no timezone supplied.\n", encoding="utf-8")
    (inputs / "correction.txt").write_text("Harbor Bulletin correction\nOpening postponed pending inspection.\n", encoding="utf-8")
    (inputs / "events.csv").write_text("TimeCreated,Description,EventId\n2026-10-01T09:00:00Z,=Synthetic literal event,10\n2026-10-01T09:00:00.1Z,Later observation,11\n2026-10-01T10:00:00,Uncertain event,12\n", encoding="utf-8")
    agent = {"format": "of-agent-events-v1", "events": [
        {"event_type": "model_text", "text": "The synthetic file was deleted."},
        {"event_type": "tool_request", "call_id": "example-1", "text": "Requested deletion, not executed here"},
        {"event_type": "tool_result", "call_id": "example-1", "text": "Reported success"},
        {"event_type": "host_observation", "text": "Supplied host export reports the file still present"}]}
    atomic_write(inputs / "agent.json", json_bytes(agent))
    paths = [inputs / name for name in ("plan.txt", "correction.txt", "events.csv", "agent.json")]
    originals = {path.name: digest(read_bytes(path)) for path in paths}
    case = output / "case"
    initialize(case, "Synthetic dependency and citation review", "Only original synthetic fixtures; no network")
    add_many(case, paths)
    add_claim(case, "An opening was planned.", ["E000001"], [], "observed", "low", "Initial notice",
              citations=[{"evidence_id": "E000001", "kind": "line", "start": 2, "end": 2,
                          "quote": "Opening planned for 09:00; no timezone supplied."}])
    add_claim(case, "An operational inference relies on that initial assessment.", ["E000001"], [],
              "inferred", "low", "Synthetic premise dependency", depends_on=["C000001"])
    add_claim(case, "A downstream assessment relies on the operational inference.", ["E000001"], [],
              "inferred", "low", "Synthetic transitive dependency", depends_on=["C000002"])
    add_claim(case, "The supplied correction postpones the opening.", ["E000002"], [], "observed", "low",
              "The initial assessment needs revision; implementation remains unknown.", supersedes="C000001",
              citations=[{"evidence_id": "E000002", "kind": "line", "start": 2, "end": 2,
                          "quote": "Opening postponed pending inspection."}])
    add_claim(case, "An intentionally incorrect citation is retained for demonstration.", ["E000001"], [],
              "unconfirmed", "low", "The citation checker must report this mismatch.",
              citations=[{"evidence_id": "E000001", "kind": "line", "start": 1, "end": 1,
                          "quote": "This text is absent from the selected line."}])
    append_review(case, {"kind": "requirement", "question_id": "Q1", "question": "Was the opening implemented?",
                        "source_categories": ["notice", "implementation"], "priority": "critical",
                        "rationale": "Implementation could change the conclusion."})
    append_review(case, {"kind": "research", "question_id": "Q1", "source_category": "notice",
                        "question": "Was the opening implemented?", "query": "Selected notices only", "scope": "Synthetic October",
                        "tool": "scripted demonstration", "status": "partial", "evidence": ["E000001", "E000002"],
                        "rationale": "Notices do not supply an implementation log."})
    for value, jurisdiction in (("EX-101", "Example North"), ("EX-202", "Example South")):
        append_review(case, {"kind": "entity", "entity_type": "organization", "label": "Harbor Example Ltd",
                            "identifiers": [{"scheme": "synthetic-register", "value": value}], "jurisdiction": jurisdiction,
                            "candidate_group": "unresolved-namesakes", "evidence": ["E000001"],
                            "rationale": "Original synthetic fixture, distinct legal identifiers.",
                            "time_context": {"valid_from": "2021-01-01", "valid_until": "2022-01-01"}})
    mapped = import_events(case, "E000003", "TimeCreated", "Description")
    save_analysis(case, case / "analysis/events.json", mapped)
    agents = agent_events(case, "E000004", "json")
    save_analysis(case, case / "analysis/agent.json", agents)
    atomic_write(case / "analysis/relations.graphml", graphml(case))
    exported, losses = timesketch_csv(case, "analysis/events.json")
    atomic_write(case / "analysis/timesketch.csv", exported)
    atomic_write(case / "analysis/exchange-losses.json", json_bytes(losses))
    status, excerpts = case_status(case), check_citations(case)
    require(status["needs_review"] == 2 and excerpts["counts"]["mismatch"] == 1, "DEMO_REVIEW_MISMATCH")
    atomic_write(case / "analysis/review-status.json", json_bytes(status))
    atomic_write(case / "analysis/citation-checks.json", json_bytes(excerpts))
    for language in ("en", "fr"):
        atomic_write(case / f"reports/report.{language}.md", render_report(case, language))
        atomic_write(case / f"reports/report.{language}.html", render_html(case, language, ["analysis/events.json", "analysis/agent.json"]))
    archive = case / "exports/private.zip"
    export_case(case, archive, "private")
    restored = output / "restored"
    restore_case(archive, restored)
    require(case_status(restored) == status and check_citations(restored) == excerpts, "DEMO_RESTORE_MISMATCH")
    require(originals == {path.name: digest(read_bytes(path)) for path in paths}, "DEMO_ORIGINAL_CHANGED")
    return {"status": "passed", "case": str(case), "verification": verify(case), "needs_review": status["needs_review"],
            "intentional_citation_mismatches": excerpts["counts"]["mismatch"], "exchange": losses,
            "plan": plan(request={"question": "Was the opening implemented?", "kinds": ["documents"], "max_steps": 2}, case=case),
            "network_calls": False, "model_calls": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a synthetic schema 3 case with dependency warnings and excerpt checks.")
    parser.add_argument("--out", required=True)
    print(json.dumps(demo(parser.parse_args().out), sort_keys=True))
