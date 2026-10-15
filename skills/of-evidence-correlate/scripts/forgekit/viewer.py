from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import html
import json

from .casefiles import load_case, verify
from .exchange import graph
from .review import checked_analysis, current, records
from .safeio import MAX_JSON, MAX_RECORDS, require, visible
from .timestamps import timestamp
from .assurance import check_citations, coverage, dependency_status

SCRIPT = """const search=document.getElementById('search');
const kind=document.getElementById('kind');
const history=document.getElementById('history');
function filter(){let count=0;document.querySelectorAll('tbody tr').forEach(row=>{
const match=row.textContent.toLowerCase().includes(search.value.toLowerCase())&&
(!kind.value||row.dataset.kind===kind.value)&&(history.checked||row.dataset.historical!=='true');
row.hidden=!match;if(match)count++;});document.getElementById('count').textContent=String(count);}
search.addEventListener('input',filter);kind.addEventListener('change',filter);
history.addEventListener('change',filter);filter();"""

STYLE = """body{font:16px system-ui,sans-serif;max-width:1200px;margin:2rem auto;padding:0 1rem;background:#faf8f4;color:#242424}
h1,h2{color:#70472b}header,p{line-height:1.6}nav{display:flex;gap:1rem;flex-wrap:wrap;align-items:center;position:sticky;top:0;background:#faf8f4;padding:1rem 0}
input,select{padding:.6rem;font:inherit;border:1px solid #777;border-radius:4px}input[type=search]{min-width:260px}
table{border-collapse:collapse;width:100%;font-size:.9rem}td,th{padding:.7rem;text-align:left;vertical-align:top;border-bottom:1px solid #ccc;overflow-wrap:anywhere}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.82rem}summary{cursor:pointer}tr[hidden]{display:none}
.scroll{overflow:auto}svg{background:white}svg text{font:12px system-ui}svg line{stroke:#777;stroke-width:1.5}.candidate{stroke-dasharray:4 3}
@media print{nav{display:none}body{max-width:none}details{display:block}}"""


def escaped(value, limit=8000):
    return html.escape(visible(value, limit), quote=True)


def render_html(case, language="en", analyses=None):
    require(language in ("en", "fr"), "UNSUPPORTED_LANGUAGE")
    verify(case)
    root, info, evidence, claims = load_case(case)
    ledger = records(root, info)
    replaced = {row.get("supersedes") for row in claims + ledger}
    entries = []
    statuses = dependency_status(claims, ledger)
    citation_checks = check_citations(case)
    for row in claims:
        state = "needs_review" if statuses[row["id"]]["status"] == "needs_review" else row["state"]
        details = {**row, "review": statuses[row["id"]], "citation_checks": [item for item in citation_checks["citations"] if item["claim_id"] == row["id"]]}
        entries.append((row["id"], "claim", state, row["text"], details))
    for row in evidence:
        entries.append((row["id"], "evidence", "preserved", row["original_name"], row))
    for row in ledger:
        entries.append((row["id"], row["kind"], row.get("status", row.get("state", "recorded")),
                        row.get("question", row.get("label", row.get("note", ""))), row))
    paths = analyses or []
    require(len(paths) <= 20 and len(set(paths)) == len(paths), "INVALID_TIMELINE_INPUTS")
    events = []
    for path in paths:
        data, fingerprint = checked_analysis(root, path, evidence)
        rows = data.get("events")
        require(isinstance(rows, list), "EVENT_ANALYSIS_REQUIRED")
        for row in rows:
            require(isinstance(row, dict) and row.get("evidence_id") == data["input"]["evidence_id"]
                    and type(row.get("record_index")) is int, "INVALID_EVENT_REFERENCE")
            require(row.get("utc") is None or timestamp(row["utc"])["time_status"] == "normalized",
                    "INVALID_EVENT_TIMESTAMP")
            events.append({**row, "analysis": path, "analysis_sha256": fingerprint})
            require(len(events) <= MAX_RECORDS, "TOO_MANY_EVENTS")
    events.sort(key=lambda row: (row.get("utc") is None,
                                datetime.fromisoformat(row["utc"]) if row.get("utc") else datetime.max.replace(tzinfo=timezone.utc)))
    for row in events:
        notes = [entry for entry in current(ledger) if entry["kind"] == "annotation"
                 and entry["analysis"] == row["analysis"] and entry["sha256"] == row["analysis_sha256"]
                 and entry["record_index"] == row["record_index"]]
        identifier = f"{row['evidence_id']}:{row['record_index']}"
        entries.append((identifier, "event", row.get("time_status", "unknown"),
                        str(row.get("utc") or row.get("original_timestamp") or "?") + " | "
                        + str(row.get("event", row.get("title", ""))) + " | "
                        + " ".join(tag for note in notes for tag in note["tags"]), {**row, "annotations": notes}))
    fr = language == "fr"
    kinds = ({"claim":"Conclusion", "evidence":"Pièce", "research":"Recherche", "entity":"Entité",
              "relation":"Relation", "annotation":"Annotation", "event":"Événement",
              "requirement":"Question", "analysis_revision":"Révision d’analyse"}
             if fr else {"claim":"Claim", "evidence":"Evidence", "research":"Research", "entity":"Entity",
                         "relation":"Relation", "annotation":"Annotation", "event":"Event",
                         "requirement":"Requirement", "analysis_revision":"Analysis revision"})
    states = ({"needs_review":"À réexaminer", "observed":"Observé", "inferred":"Déduit", "unconfirmed":"Non confirmé",
               "preserved":"Conservé", "recorded":"Enregistré", "candidate":"Candidat",
               "not_searched":"Non recherché", "no_result":"Sans résultat", "partial":"Partiel",
               "unavailable":"Indisponible", "completed":"Terminé", "normalized":"Heure normalisée",
               "timezone_unknown":"Fuseau inconnu", "missing":"Heure absente", "invalid":"Heure invalide"}
              if fr else {"needs_review":"Needs review"})
    title = "Relecture du dossier" if fr else "Case review"
    notice = ("Dossier privé. Références et relations déclarées par l'analyste ; authenticité et pertinence non établies. "
              "Les données sont affichées comme texte. Aucun accès réseau. Chronologies : uniquement les analyses sélectionnées."
              if fr else "Private case. Analyst-supplied references and relations; authenticity and relevance are not established. "
              "Evidence is displayed as text. No network access. Timelines include only selected analyses.")
    rows_html = []
    for identifier, kind, state, text, details in entries:
        rows_html.append(f'<tr data-kind="{kind}" data-historical="{str(identifier in replaced).lower()}">'
                         f'<td>{escaped(identifier)}</td><td>{kinds[kind]}<br>{escaped(states.get(state,state))}</td><td>{escaped(text)}'
                         f'<details><summary>{"Détails" if fr else "Details"}</summary>'
                         f'<pre>{escaped(json.dumps(details, ensure_ascii=False, indent=2), MAX_JSON)}</pre>'
                         '</details></td></tr>')
    network = graph(case)
    nodes, edges = network["nodes"], network["edges"]
    if len(nodes) <= 150 and len(edges) <= 500:
        positions = {node["id"]: (110 + (index % 4) * 280, 70 + (index // 4) * 120)
                     for index, node in enumerate(nodes)}
        drawing = [f'<svg role="img" aria-label="Evidence graph" width="1120" height="{max(180, ((len(nodes)+3)//4)*120)}">']
        for edge in edges:
            x1, y1 = positions[edge["source"]]
            x2, y2 = positions[edge["target"]]
            drawing.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                           f'class="{edge["state"]}"><title>{escaped(edge["source"])} → {escaped(edge["target"])}: '
                           f'{escaped(edge["label"])}; {escaped(edge["state"])}; {escaped(", ".join(edge["evidence"]))}</title></line>')
        for node in nodes:
            x, y = positions[node["id"]]
            drawing.append(f'<g><title>{escaped(node["label"])}</title><rect x="{x-100}" y="{y-24}" width="200" '
                           f'height="48" rx="6" fill="#eee5d9" stroke="#70472b"/><text x="{x-90}" y="{y-5}">'
                           f'{node["id"]} · {node["kind"]}</text><text x="{x-90}" y="{y+14}">'
                           f'{escaped(node["label"], 24)}</text></g>')
        drawing.append('</svg>')
        graph_html = "".join(drawing)
    else:
        graph_html = f'<p>Graph display limit: {len(nodes)} nodes, {len(edges)} edges. Use the graph export.</p>'
    edge_list = '<details><summary>Relations</summary><ul>' + ''.join(
        f'<li>{escaped(edge["source"])} → {escaped(edge["target"])}: {escaped(edge["label"])} '
        f'[{escaped(edge["state"])}] {escaped(", ".join(edge["evidence"]))}</li>' for edge in edges) + '</ul></details>'
    script_hash = base64.b64encode(hashlib.sha256(SCRIPT.encode()).digest()).decode()
    style_hash = base64.b64encode(hashlib.sha256(STYLE.encode()).digest()).decode()
    csp = f"default-src 'none'; script-src 'sha256-{script_hash}'; style-src 'sha256-{style_hash}'; base-uri 'none'; form-action 'none'; connect-src 'none'"
    page = (f'<!doctype html><html lang="{language}"><head><meta charset="utf-8">'
            f'<meta http-equiv="Content-Security-Policy" content="{html.escape(csp, quote=True)}">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>'
            f'<style>{STYLE}</style></head><body><header><h1>{title}: {escaped(info["title"])}</h1>'
            f'<p>{escaped(info["scope"])}</p><p>{notice}</p></header><nav>'
            f'<label>{"Recherche" if fr else "Search"} <input id="search" type="search"></label>'
            f'<label>Type <select id="kind"><option value="">{"Tous" if fr else "All"}</option>'
            + ''.join(f'<option value="{kind}">{label}</option>' for kind,label in kinds.items())
            + f'</select></label><label><input type="checkbox" id="history">{"Historique" if fr else "History"}</label>'
            '<output id="count" aria-live="polite"></output></nav>'
            f'<div class="scroll"><table><thead><tr><th>ID</th><th>Type / {"État" if fr else "Status"}</th><th>Observation</th></tr></thead><tbody>'
            + ''.join(rows_html) + '</tbody></table></div>'
            + f'<h2>{"Couverture déclarée" if fr else "Declared coverage"}</h2><pre>{escaped(json.dumps(coverage(ledger), ensure_ascii=False, indent=2), MAX_JSON)}</pre>'
            + f'<h2>{"Contrôle des citations" if fr else "Citation checks"}</h2><pre>{escaped(json.dumps(citation_checks["counts"], ensure_ascii=False))}</pre><h2>Relations</h2><div class="scroll">'
            + graph_html + '</div>' + edge_list + f'<script>{SCRIPT}</script></body></html>')
    data = page.encode()
    require(len(data) <= MAX_JSON, "REPORT_TOO_LARGE")
    return data
