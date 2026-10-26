from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(ROOT / "skills/of-case-start/scripts"))
from forgekit.analysis import save_analysis
from forgekit.assurance import check_citations
from forgekit.casefiles import add_claim, add_evidence, initialize, verify
from forgekit.public_imports import bodacc_history, transcript, wayback_index
from forgekit.reporting import export_case, restore_case
from forgekit.safeio import atomic_write, json_bytes, require, safe_path
from forgekit.viewer import render_html


def demo(destination):
    output = safe_path(destination, exists=False)
    require(not output.exists(), "OUTPUT_EXISTS")
    output.mkdir(mode=0o700)
    inputs = output / "inputs"
    inputs.mkdir(mode=0o700)
    case = output / "case"
    initialize(case, "Synthetic public exports", "Original synthetic fixtures only, no acquisition")
    fixtures = {
        "cdx.json": json_bytes([["original", "timestamp", "statuscode"],
                                ["https://example.org/notice", "20261012090000", "200"],
                                ["https://example.org/notice", "20261011090000", "200"]]),
        "bodacc.json": json_bytes({"total_count": 3, "results": [
            {"id": "SYNTHETIC-NOTICE-A", "registre": ["000 000 000"],
             "dateparution": "2026-10-12", "dateacte": "2026-10-01",
             "familleavis_lib": "Synthetic registration", "commercant": "Harbor Example"}]}),
        "captions.txt": b"WEBVTT\n\n00:01.000 --> 00:12.000\nThe opening remains a plan.\n",
    }
    ids = {}
    for name, content in fixtures.items():
        atomic_write(inputs / name, content)
        ids[name] = add_evidence(case, inputs / name)["id"]
    analyses = {
        "captures": wayback_index(case, ids["cdx.json"], "https://example.org/notice"),
        "notices": bodacc_history(case, ids["bodacc.json"], "000000000", "dateacte"),
        "transcript": transcript(case, ids["captions.txt"], "vtt", "unknown", "unknown", "en"),
    }
    hashes = {}
    for name, value in analyses.items():
        hashes[name] = save_analysis(case, case / "analysis" / (name + ".json"), value)["sha256"]
    for name, identifier, kind, start, end, quote, selected_field in (
            ("captures", ids["cdx.json"], "record", 1, 1, "20261011090000", "capture_timestamp"),
            ("notices", ids["bodacc.json"], "record", 0, 0, "SYNTHETIC-NOTICE-A", "notice_id"),
            ("transcript", ids["captions.txt"], "time_ms", 1000, 12000, "The opening remains a plan.", None)):
        citation = {"evidence_id": identifier, "kind": kind, "start": start, "end": end,
                    "quote": quote, "analysis": "analysis/" + name + ".json", "sha256": hashes[name]}
        if selected_field:
            citation["field"] = selected_field
        add_claim(case, "The supplied " + name + " contains the cited value.", [identifier], [],
                  "observed", "low", "Synthetic text only, external facts and audio unverified", citations=[citation])
    citations = check_citations(case)
    require(all(row["status"] == "excerpt_found" for row in citations["citations"]), "DEMO_CITATION_FAILED")
    for language in ("en", "fr"):
        atomic_write(case / "reports" / ("report." + language + ".html"),
                     render_html(case, language, ["analysis/" + name + ".json" for name in analyses]))
    export_case(case, case / "exports/private.zip", "private")
    restore_case(case / "exports/private.zip", output / "restored")
    return {"status": "passed", "verification": verify(case), "restored": verify(output / "restored"),
            "citations": len(citations["citations"]), "network_calls": False, "model_calls": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a synthetic local public-export and transcript workflow.")
    parser.add_argument("--out", required=True)
    print(json.dumps(demo(parser.parse_args().out), sort_keys=True))
