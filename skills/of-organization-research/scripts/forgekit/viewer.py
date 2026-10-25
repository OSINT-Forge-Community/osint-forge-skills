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
from .snapshot import read_operation

SCRIPT = """const search=document.getElementById('search');
const kind=document.getElementById('kind');
const focus=document.getElementById('focus');
const history=document.getElementById('history');
const count=document.getElementById('count');
const normalize=value=>value.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
const rows=Array.from(document.querySelectorAll('#records tbody tr'),row=>({
row,text:normalize(row.textContent),kind:row.dataset.kind,historical:row.dataset.historical==='true',
review:row.dataset.review==='true',citation:row.dataset.citation==='true',uncertain:row.dataset.uncertain==='true'}));
function filter(){const terms=normalize(search.value).trim().split(/\\s+/).filter(Boolean);let shown=0;
for(const item of rows){const match=terms.every(term=>item.text.includes(term))&&
(!kind.value||item.kind===kind.value)&&(history.checked||!item.historical)&&
(!focus.value||item[focus.value]);item.row.hidden=!match;if(match)shown++;}
count.textContent=shown+' / '+rows.length+' '+count.dataset.label;
document.getElementById('empty').hidden=shown!==0;}
let pending;search.addEventListener('input',()=>{clearTimeout(pending);pending=setTimeout(filter,80);});
for(const control of [kind,focus,history])control.addEventListener('change',filter);
document.getElementById('reset').addEventListener('click',()=>{
search.value='';kind.value='';focus.value='';history.checked=false;filter();search.focus();});
document.getElementById('theme').addEventListener('change',event=>{
document.documentElement.dataset.theme=event.target.value;});
document.getElementById('print').addEventListener('click',()=>window.print());
for(const button of document.querySelectorAll('[data-focus]'))button.addEventListener('click',()=>{
search.value='';kind.value='';focus.value=button.dataset.focus;history.checked=false;filter();
document.getElementById('records-heading').scrollIntoView({block:'start'});focus.focus({preventScroll:true});});
for(const control of document.querySelectorAll('[data-control]'))control.disabled=false;
filter();"""

STYLE = """:root{color-scheme:light;--bg:#f3f5f7;--surface:#fff;--soft:#eef3f4;--ink:#152b35;--muted:#526773;--line:#ced9de;--brand:#00655f;--brand-soft:#e0f2ed;--warn:#89430b;--warn-soft:#fff0d9;--bad:#a72d37;--bad-soft:#ffebed;--ring:#007a73}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){color-scheme:dark;--bg:#101c24;--surface:#172832;--soft:#20343f;--ink:#e6eff2;--muted:#acc1cb;--line:#3c535f;--brand:#7edbcb;--brand-soft:#203f3e;--warn:#ffca81;--warn-soft:#49341d;--bad:#ffb0b5;--bad-soft:#482d37;--ring:#88e3d3}}
:root[data-theme=dark]{color-scheme:dark;--bg:#101c24;--surface:#172832;--soft:#20343f;--ink:#e6eff2;--muted:#acc1cb;--line:#3c535f;--brand:#7edbcb;--brand-soft:#203f3e;--warn:#ffca81;--warn-soft:#49341d;--bad:#ffb0b5;--bad-soft:#482d37;--ring:#88e3d3}
*{box-sizing:border-box}html{scroll-padding-top:1rem}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 system-ui,-apple-system,sans-serif}main,.page-header,.page-footer{max-width:1240px;margin:auto;padding:1.5rem 2rem}h1,h2,h3,p{margin:0}h1{font-size:clamp(1.65rem,4vw,2.65rem);line-height:1.15;letter-spacing:-.035em;overflow-wrap:anywhere}h2{font-size:1.25rem;letter-spacing:-.02em}h3{font-size:1rem}a{color:var(--brand);text-underline-offset:.2em}button,input,select{font:inherit}button,select,input[type=search]{min-height:44px;border:1px solid var(--line);border-radius:9px;background:var(--surface);color:var(--ink);padding:.6rem .75rem}button{cursor:pointer}button:hover{border-color:var(--brand);background:var(--brand-soft)}:focus-visible{outline:3px solid var(--ring);outline-offset:3px}button:disabled{cursor:default;opacity:.6}input[type=checkbox]{width:1.1rem;height:1.1rem;accent-color:var(--brand)}.skip{position:absolute;left:1rem;top:-5rem;z-index:5;background:var(--surface);padding:.7rem}.skip:focus{top:1rem}.page-header{padding-top:2rem;padding-bottom:0}.topline,.heading-line,.footer-line{display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap}.brand{font-size:.75rem;font-weight:800;letter-spacing:.13em;color:var(--brand)}.tools{display:flex;align-items:center;gap:.5rem}.tools label{color:var(--muted);font-size:.8rem}.tools select{min-width:0}.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:.7rem;font-weight:750;color:var(--muted)}.title-block{padding:2rem 0 1.25rem}.title-block h1{margin:.5rem 0 .8rem}.scope{max-width:85ch;color:var(--muted);white-space:pre-wrap;overflow-wrap:anywhere}.privacy{border-left:3px solid var(--brand);background:var(--brand-soft);padding:.75rem 1rem;border-radius:0 9px 9px 0;font-size:.85rem}.section-nav{display:flex;gap:1.5rem;flex-wrap:wrap;padding:1rem 0 0;font-weight:650;font-size:.85rem}.section-nav a{text-decoration:none}.section-nav a:hover{text-decoration:underline}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1rem}.stat{background:var(--surface);border:1px solid var(--line);border-radius:13px;padding:1rem 1.15rem;display:flex;align-items:flex-start;flex-direction:column;text-align:left}.stat strong{font-size:2rem;line-height:1.2;font-weight:750;letter-spacing:-.04em}.stat-label{font-size:.85rem;font-weight:700;margin:.35rem 0 .15rem}.stat small{color:var(--muted);font-size:.75rem}.stat.attention strong{color:var(--warn)}.panel{margin-top:1.5rem;border:1px solid var(--line);border-radius:14px;background:var(--surface);overflow:hidden}.panel-heading{padding:1.2rem 1.35rem;border-bottom:1px solid var(--line)}.panel-heading p,.hint{font-size:.83rem;color:var(--muted);margin-top:.3rem}.panel-body{padding:1.2rem 1.35rem}.filters{display:flex;align-items:flex-end;gap:.85rem;flex-wrap:wrap;padding:1rem 1.35rem;background:var(--soft)}.field{display:flex;flex-direction:column;gap:.35rem;font-size:.8rem;font-weight:650}.field.search{flex:1;min-width:200px}.field select,.field input{width:100%;font-weight:400}.check{display:flex;align-items:center;gap:.45rem;min-height:44px;font-size:.85rem}.results-line{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;padding:.7rem 1.35rem;border-bottom:1px solid var(--line);font-size:.8rem;color:var(--muted)}.scroll{overflow-x:auto;max-width:100%}table{border-collapse:collapse;width:100%;font-size:.88rem}caption{text-align:left;padding:1rem 1.35rem;font-weight:650}td,th{padding:.9rem 1.35rem;text-align:left;vertical-align:top;border-bottom:1px solid var(--line);overflow-wrap:anywhere}th{font-size:.7rem;font-weight:750;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);background:var(--soft)}tbody tr:last-child td{border-bottom:0}.record-id{width:110px;font: .8rem ui-monospace,SFMono-Regular,monospace;white-space:nowrap}.record-state{width:175px}.record-state>span:first-child{display:block;font-weight:650;margin-bottom:.35rem}.observation{white-space:pre-wrap;overflow-wrap:anywhere;font-weight:600}.badge{display:inline-block;border-radius:6px;background:var(--soft);color:var(--muted);font-size:.73rem;font-weight:650;line-height:1.5;padding:.17rem .45rem;margin:.12rem .2rem .12rem 0}.badge.good{color:var(--brand);background:var(--brand-soft)}.badge.warn{color:var(--warn);background:var(--warn-soft)}.badge.bad{color:var(--bad);background:var(--bad-soft)}.history-label{display:block;color:var(--muted);font: .72rem system-ui,sans-serif;margin-top:.4rem}.record-context{font-size:.8rem;color:var(--muted);margin-top:.5rem;overflow-wrap:anywhere}.record-context strong{color:var(--ink);font-weight:600}.review-reasons{border-left:2px solid var(--warn);padding-left:.65rem;margin-top:.6rem;color:var(--warn);font-size:.8rem}.review-reasons ul{margin:.2rem 0;padding-left:1.2rem}.raw-record{margin-top:.6rem}summary{cursor:pointer;color:var(--brand);font-size:.8rem;font-weight:650}pre{white-space:pre-wrap;overflow-wrap:anywhere;font: .74rem/1.5 ui-monospace,SFMono-Regular,monospace;background:var(--soft);padding:.8rem;border-radius:8px;max-height:400px;overflow:auto}details[open]>summary{margin-bottom:.7rem}.empty{padding:2.5rem 1.35rem;text-align:center;color:var(--muted)}.coverage-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}.coverage-card{border:1px solid var(--line);border-radius:10px;padding:1rem;min-width:0;overflow-wrap:anywhere}.coverage-card h3{margin:.25rem 0 .75rem}.category{padding:.6rem 0;border-top:1px solid var(--line)}.category-name{font-size:.85rem;font-weight:650}.category p{font-size:.75rem;color:var(--muted)}.citation-stats{display:flex;gap:.65rem;flex-wrap:wrap;margin-bottom:1rem}.citation-stats .badge{padding:.5rem .7rem}.graph-detail{margin-top:1rem}svg{display:block;background:var(--surface)}svg text{font:12px system-ui,sans-serif;fill:var(--ink)}svg rect{fill:var(--soft);stroke:var(--line)}svg line{stroke:var(--muted);stroke-width:1.5}.candidate{stroke-dasharray:4 3}.edge-list{font-size:.8rem;overflow-wrap:anywhere;padding-left:1.25rem}.page-footer{font-size:.78rem;color:var(--muted);padding-top:0}.print-note{display:none}[hidden]{display:none!important}
@media(max-width:760px){main,.page-header,.page-footer{padding-left:1rem;padding-right:1rem}.stats{grid-template-columns:repeat(2,minmax(0,1fr));gap:.65rem}.stat{padding:.85rem}.stat strong{font-size:1.7rem}.coverage-grid{grid-template-columns:1fr}.panel-heading,.panel-body,.filters{padding:1rem}.filters .field{flex:1;min-width:150px}.filters .field.search{flex-basis:100%}.filters .check{flex:1}.results-line{padding:.7rem 1rem}.records-table thead{display:none}.records-table,.records-table tbody,.records-table tr,.records-table td{display:block;width:auto}.records-table tr{padding:1rem;border-bottom:1px solid var(--line)}.records-table td{padding:0;border:0}.records-table td.record-id{display:inline-block;margin:0 .6rem .45rem 0}.records-table .history-label{display:inline;margin-left:.4rem}.records-table .record-state{margin-bottom:.45rem}.records-table .record-state>span:first-child{display:inline;margin-right:.5rem}.records-table .record-state .badge{margin-top:0}.topline{align-items:flex-start}.tools{flex-wrap:wrap}.title-block{padding-top:1.5rem}.section-nav{gap:1rem}td,th{padding:.7rem}.citation-table{min-width:520px}}
@media(prefers-reduced-motion:no-preference){button,select{transition:background-color .15s,border-color .15s}}
@media print{:root,:root[data-theme],:root:not([data-theme=light]){color-scheme:light;--bg:#fff;--surface:#fff;--soft:#f3f3f3;--ink:#111;--muted:#444;--line:#bbb;--brand:#174d49;--brand-soft:#f2f5f4;--warn:#713400;--warn-soft:#fff;--bad:#8b1821;--bad-soft:#fff}body{font-size:10pt}.tools,.section-nav,.filters,.results-line,.raw-record,.skip,.empty,.graph-detail,.screen-note{display:none!important}.print-note{display:block}.page-header,main,.page-footer{max-width:none;padding:0}.title-block{padding:1rem 0}.stats{gap:.5rem;margin-top:1rem}.panel{overflow:visible;break-inside:auto}.panel-heading{break-after:avoid}.records-table tr[hidden]{display:table-row!important}.records-table,.records-table tbody{display:table-row-group}.records-table{display:table}.records-table thead{display:table-header-group}.records-table tr{display:table-row;break-inside:avoid}.records-table td{display:table-cell;width:auto;padding:.6rem;border-bottom:1px solid var(--line)}.records-table td.record-id{display:table-cell}.scroll{overflow:visible}pre{max-height:none}a{color:inherit}.coverage-grid{display:block}.coverage-card{margin-bottom:.7rem;break-inside:avoid}.page-footer{margin-top:1rem}}
"""


def escaped(value, limit=8000):
    return html.escape(visible(value, limit), quote=True)


def badge(value, labels, tone=""):
    return f'<span class="badge {tone}">{escaped(labels.get(value, value))}</span>'


@read_operation
def render_html(case, language="en", analyses=None):
    require(language in ("en", "fr"), "UNSUPPORTED_LANGUAGE")
    verify(case)
    root, info, evidence, claims = load_case(case)
    ledger = records(root, info)
    replaced = {row.get("supersedes") for row in claims + ledger}
    replaced.update(row["id"] for row in ledger if row.get("retired"))
    from .investigation import investigation_status
    test_statuses = {row["id"]: row for row in investigation_status(ledger)["tests"]}
    statuses = dependency_status(claims, ledger)
    citation_checks = check_citations(case)
    citations_by_claim = {}
    for item in citation_checks["citations"]:
        citations_by_claim.setdefault(item["claim_id"], []).append(item)
    annotations = {}
    for row in current(ledger):
        if row["kind"] == "annotation":
            annotations.setdefault((row["analysis"], row["sha256"], row["record_index"]), []).append(row)
    entries = []
    for row in claims:
        state = "needs_review" if statuses[row["id"]]["status"] == "needs_review" else row["state"]
        details = {**row, "review": statuses[row["id"]], "citation_checks": citations_by_claim.get(row["id"], [])}
        entries.append((row["id"], "claim", state, row["text"], details))
    for row in evidence:
        entries.append((row["id"], "evidence", "preserved", row["original_name"], row))
    for row in ledger:
        state = "retired" if row.get("retired") else "needs_review" if test_statuses.get(row["id"], {}).get("needs_review") else row.get("status", row.get("state", "recorded"))
        text = row.get("question", row.get("label", row.get("note", row.get("statement", row.get("action", row.get("basis", ""))))))
        entries.append((row["id"], row["kind"], state, text, row))
    paths = analyses or []
    require(len(paths) <= 20 and len(set(paths)) == len(paths), "INVALID_TIMELINE_INPUTS")
    events = []
    for path in paths:
        data, fingerprint = checked_analysis(root, path, evidence)
        rows = data.get("events")
        require(isinstance(rows, list), "EVENT_ANALYSIS_REQUIRED")
        for row in rows:
            require(isinstance(row, dict) and row.get("evidence_id") == data["input"]["evidence_id"]
                    and type(row.get("record_index")) is int and row["record_index"] >= 0, "INVALID_EVENT_REFERENCE")
            require(isinstance(row.get("time_status", "unknown"), str)
                    and 0 < len(row.get("time_status", "unknown")) <= 100
                    and (row.get("utc") is None or timestamp(row["utc"])["time_status"] == "normalized"),
                    "INVALID_EVENT_TIMESTAMP")
            events.append({**row, "analysis": path, "analysis_sha256": fingerprint})
            require(len(events) <= MAX_RECORDS, "TOO_MANY_EVENTS")
    events.sort(key=lambda row: (row.get("utc") is None,
                                datetime.fromisoformat(row["utc"]) if row.get("utc") else datetime.max.replace(tzinfo=timezone.utc)))
    for row in events:
        notes = annotations.get((row["analysis"], row["analysis_sha256"], row["record_index"]), [])
        identifier = f"{row['evidence_id']}:{row['record_index']}"
        entries.append((identifier, "event", row.get("time_status", "unknown"),
                        str(row.get("utc") or row.get("original_timestamp") or "?") + " | "
                        + str(row.get("event", row.get("title", ""))) + " | "
                        + " ".join(tag for note in notes for tag in note["tags"]), {**row, "annotations": notes}))
    fr = language == "fr"
    def tr(en, french):
        return french if fr else en
    kinds = {"claim":tr("Claim", "Conclusion"), "evidence":tr("Evidence", "Pièce"),
             "research":tr("Research", "Recherche"), "entity":tr("Entity", "Entité"),
             "relation":tr("Relation", "Relation"), "annotation":tr("Annotation", "Annotation"),
             "event":tr("Event", "Événement"), "requirement":tr("Requirement", "Question"),
             "analysis_revision":tr("Analysis revision", "Révision d’analyse"),
             "hypothesis":tr("Hypothesis", "Hypothèse"), "test":tr("Discriminating test", "Test discriminant"),
             "origin":tr("Assertion origin", "Origine de l'assertion")}
    states = {key:tr(en, french) for key, en, french in (
        ("needs_review", "Needs review", "À réexaminer"), ("observed", "Observed", "Observé"),
        ("inferred", "Inferred", "Déduit"), ("unconfirmed", "Unconfirmed", "Non confirmé"),
        ("preserved", "Preserved", "Conservé"), ("recorded", "Recorded", "Enregistré"),
        ("candidate", "Candidate", "Candidat"), ("not_searched", "Not searched", "Non recherché"),
        ("no_result", "No result", "Sans résultat"), ("partial", "Partial", "Partiel"),
        ("unavailable", "Unavailable", "Indisponible"), ("completed", "Completed", "Terminé"),
        ("normalized", "Normalized time", "Heure normalisée"), ("timezone_unknown", "Unknown timezone", "Fuseau inconnu"),
        ("missing", "Missing time", "Heure absente"), ("invalid", "Invalid time", "Heure invalide"),
        ("unknown", "Unknown time", "Heure inconnue"), ("excerpt_found", "Exact excerpt found", "Extrait exact retrouvé"),
        ("locator_found", "Locator found", "Repère retrouvé"), ("mismatch", "Mismatch", "Discordance"),
        ("unverifiable", "Unverifiable", "Invérifiable"), ("critical", "Critical", "Critique"),
        ("supporting", "Supporting", "Complémentaire"), ("current", "Current", "Actuel"),
        ("low", "Low", "Faible"), ("medium", "Medium", "Moyenne"), ("high", "High", "Élevée"),
        ("supported", "Supported", "Appuyée"), ("rejected", "Rejected", "Écartée"),
        ("unresolved", "Unresolved", "Non résolue"), ("planned", "Planned", "Prévu"),
        ("blocked", "Blocked", "Bloqué"), ("inconclusive", "Inconclusive", "Non concluant"),
        ("retired", "Withdrawn", "Retiré"))}
    title = tr("Case review", "Relecture du dossier")
    notice = tr("Private case. Analyst-supplied references and relations; authenticity and relevance are not established. "
                "Evidence is displayed as text. No network access. Timelines include only selected analyses.",
                "Dossier privé. Références et relations déclarées par l'analyste ; authenticité et pertinence non établies. "
                "Les données sont affichées comme texte. Aucun accès réseau. Chronologies : uniquement les analyses sélectionnées.")
    rows_html = []
    for identifier, kind, state, text, details in entries:
        historical = identifier in replaced
        checks = details.get("citation_checks", [])
        citation_issue = any(item["status"] in ("mismatch", "unverifiable") for item in checks)
        uncertain = kind == "event" and details.get("utc") is None
        context = []
        if kind == "claim":
            context.append(f'<strong>{tr("Analyst confidence", "Confiance déclarée")}</strong>: '
                           f'{escaped(states[details["confidence"]])}')
            for key, label in (("supports", tr("Supports", "Appuis")), ("contradicts", tr("Contradicts", "Contradictions")),
                               ("depends_on", tr("Premises", "Prémisses"))):
                if details.get(key):
                    context.append(f'<strong>{label}</strong>: {escaped(", ".join(details[key]))}')
        if kind == "event":
            context.append(escaped(details["analysis"]))
            context.extend(escaped(note["note"]) for note in details["annotations"])
        if details.get("rationale"):
            context.append(escaped(details["rationale"]))
        if kind in ("hypothesis", "test", "origin"):
            for key, en, french in (("statement", "Statement", "Proposition"), ("prediction", "Prediction", "Prédiction"),
                    ("expected", "Expected observation", "Observation attendue"), ("observation", "Recorded observation", "Observation enregistrée"),
                    ("hypothesis", "Hypothesis", "Hypothèse"), ("outcome", "Declared outcome", "Résultat déclaré"),
                    ("origin_group", "Upstream origin", "Origine amont"), ("relationship", "Origin relationship", "Relation d'origine")):
                if key in details:
                    context.append(f'<strong>{tr(en, french)}</strong>: {escaped(details[key])}')
        reason_html = []
        for reason in details.get("review", {}).get("reasons", []):
            if reason["kind"] == "claim_revised":
                message = f'{tr("Revised premise", "Prémisse corrigée")}: {" → ".join(reason["path"])}; '
                message += f'{tr("replacement", "remplacement")}: {reason["replacement"]}'
            else:
                message = f'{tr("Revised analysis", "Analyse corrigée")}: {reason["analysis"]}; {reason["revision"]}'
            reason_html.append(f'<li>{escaped(message)}</li>')
        reasons = ('<div class="review-reasons"><ul>' + ''.join(reason_html) + '</ul></div>') if reason_html else ''
        check_badges = ''.join(badge(item["status"], states, "bad" if item["status"] == "mismatch" else
                                     "warn" if item["status"] == "unverifiable" else "good") for item in checks)
        tone = "warn" if state in ("needs_review", "partial", "not_searched", "unavailable") or uncertain else ""
        rows_html.append(f'<tr data-kind="{kind}" data-historical="{str(historical).lower()}" '
                         f'data-review="{str(state == "needs_review").lower()}" data-citation="{str(citation_issue).lower()}" '
                         f'data-uncertain="{str(uncertain).lower()}"><td class="record-id">{escaped(identifier)}'
                         + (f'<span class="history-label">{tr("Historical", "Historique")}</span>' if historical else '')
                         + f'</td><td class="record-state"><span>{kinds[kind]}</span>{badge(state, states, tone)}</td>'
                         f'<td><p class="observation">{escaped(text)}</p>'
                         + ''.join(f'<p class="record-context">{item}</p>' for item in context) + reasons
                         + (f'<div class="record-context">{check_badges}</div>' if checks else '')
                         + f'<details class="raw-record"><summary>{tr("Recorded details", "Détails enregistrés")}</summary>'
                         f'<pre>{escaped(json.dumps(details, ensure_ascii=False, indent=2), MAX_JSON)}</pre></details></td></tr>')
    declared = coverage(ledger)
    coverage_cards = []
    for requirement in declared["requirements"]:
        categories = []
        for category in requirement["categories"]:
            labels = ''.join(badge(status, states, "good" if status == "completed" else "warn")
                             for status in category["statuses"])
            references = ", ".join(category["research_ids"]) or tr("No recorded search", "Aucune recherche enregistrée")
            categories.append(f'<div class="category"><p class="category-name">{escaped(category["category"])}</p>'
                              f'<div>{labels}</div><p>{escaped(references)}</p></div>')
        coverage_cards.append(f'<article class="coverage-card"><span class="eyebrow">{escaped(requirement["question_id"])}</span> '
                              f'{badge(requirement["priority"], states)}<h3>{escaped(requirement["question"])}</h3>'
                              + ''.join(categories) + '</article>')
    coverage_html = ('<div class="coverage-grid">' + ''.join(coverage_cards) + '</div>') if coverage_cards else (
        f'<p class="hint">{tr("No requirements declared. Coverage cannot be assessed from this case.", "Aucune question déclarée. La couverture ne peut pas être évaluée à partir de ce dossier.")}</p>')
    citation_rows = []
    for item in citation_checks["citations"]:
        state = item["status"]
        historical = item["claim_id"] in replaced
        citation_rows.append(f'<tr><td class="record-id">{escaped(item["claim_id"])}'
                             + (f'<span class="history-label">{tr("Historical", "Historique")}</span>' if historical else '')
                             + f'</td><td>{escaped(item["evidence_id"])} · #{item["citation_index"] + 1}</td>'
                             f'<td>{badge(state, states, "bad" if state == "mismatch" else "warn" if state == "unverifiable" else "good")}'
                             + (f'<p class="hint">{escaped(item["code"])}</p>' if item.get("code") else '') + '</td></tr>')
    citation_stats = ''.join(f'<span class="badge {"bad" if state == "mismatch" else "warn" if state == "unverifiable" else "good"}">'
                             f'{count} {states[state]}</span>' for state, count in citation_checks["counts"].items())
    citation_html = ('<div class="scroll"><table class="citation-table"><thead><tr>'
                     f'<th>{kinds["claim"]}</th><th>{tr("Evidence / citation", "Pièce / citation")}</th>'
                     f'<th>{tr("Result", "Résultat")}</th></tr></thead><tbody>' + ''.join(citation_rows) + '</tbody></table></div>') if citation_rows else (
        f'<p class="hint">{tr("No precise citations recorded. Add locators to check their bytes.", "Aucune citation précise enregistrée. Ajouter des repères pour vérifier leurs octets.")}</p>')
    network = graph(case)
    nodes, edges = network["nodes"], network["edges"]
    if len(nodes) <= 150 and len(edges) <= 500:
        positions = {node["id"]: (110 + (index % 4) * 280, 70 + (index // 4) * 120)
                     for index, node in enumerate(nodes)}
        drawing = [f'<svg role="img" aria-label="{tr("Evidence and relation graph", "Graphe des pièces et relations")}" '
                   f'width="1120" height="{max(180, ((len(nodes)+3)//4)*120)}">']
        for edge in edges:
            x1, y1 = positions[edge["source"]]
            x2, y2 = positions[edge["target"]]
            drawing.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                           f'class="{escaped(edge["state"])}"><title>{escaped(edge["source"])} → {escaped(edge["target"])}: '
                           f'{escaped(edge["label"])}; {escaped(edge["state"])}; {escaped(", ".join(edge["evidence"]))}</title></line>')
        for node in nodes:
            x, y = positions[node["id"]]
            drawing.append(f'<g><title>{escaped(node["label"])}</title><rect x="{x-100}" y="{y-24}" width="200" '
                           f'height="48" rx="8"/><text x="{x-90}" y="{y-5}">{escaped(node["id"])} · '
                           f'{escaped(kinds.get(node["kind"], node["kind"]))}</text><text x="{x-90}" y="{y+14}">'
                           f'{escaped(node["label"], 24)}</text></g>')
        drawing.append('</svg>')
        graph_html = ''.join(drawing)
    else:
        graph_html = f'<p class="hint">{tr("Graph display limit reached. Use the graph export.", "Limite d’affichage du graphe atteinte. Utiliser l’export du graphe.")}</p>'
    edge_list = '<ul class="edge-list">' + ''.join(
        f'<li>{escaped(edge["source"])} → {escaped(edge["target"])}: {escaped(edge["label"])} '
        f'[{escaped(states.get(edge["state"], edge["state"]))}] {escaped(", ".join(edge["evidence"]))}</li>' for edge in edges) + '</ul>'
    active_claims = [row for row in claims if row["id"] not in replaced]
    issue_count = sum(any(item["status"] in ("mismatch", "unverifiable") for item in citations_by_claim.get(row["id"], []))
                      for row in active_claims)
    needs_review = sum(row["status"] == "needs_review" for row in statuses.values())
    stats = ((len(evidence), tr("Preserved evidence", "Pièces conservées"), tr("Registered originals", "Originaux enregistrés"), ""),
             (len(active_claims), tr("Current claims", "Conclusions actuelles"), tr("History retained below", "Historique conservé ci-dessous"), ""),
             (needs_review, tr("Needs review", "À réexaminer"), tr("Revised premises or analyses", "Prémisses ou analyses corrigées"), "review"),
             (issue_count, tr("Citation issues", "Citations à vérifier"), tr("Current claims affected", "Conclusions actuelles concernées"), "citation"))
    stats_html = []
    for value, label, description, action in stats:
        tag = "button" if action else "div"
        attrs = f' type="button" data-control disabled data-focus="{action}"' if action else ''
        stats_html.append(f'<{tag} class="stat{" attention" if value and action else ""}"{attrs}>'
                          f'<strong>{value}</strong><span class="stat-label">{label}</span><small>{description}</small></{tag}>')
    script_hash = base64.b64encode(hashlib.sha256(SCRIPT.encode()).digest()).decode()
    style_hash = base64.b64encode(hashlib.sha256(STYLE.encode()).digest()).decode()
    csp = f"default-src 'none'; script-src 'sha256-{script_hash}'; style-src 'sha256-{style_hash}'; base-uri 'none'; form-action 'none'; connect-src 'none'"
    page = (f'<!doctype html><html lang="{language}"><head><meta charset="utf-8">'
            f'<meta http-equiv="Content-Security-Policy" content="{html.escape(csp, quote=True)}">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}: {escaped(info["title"])}</title>'
            f'<style>{STYLE}</style></head><body><a class="skip" href="#records">{tr("Skip to records", "Aller aux entrées")}</a>'
            f'<header class="page-header"><div class="topline"><span class="brand">OSINT FORGE / {tr("PRIVATE REVIEW", "RELECTURE PRIVÉE")}</span>'
            f'<div class="tools"><label for="theme">{tr("Appearance", "Apparence")}</label><select id="theme" data-control disabled>'
            f'<option value="auto">{tr("System", "Système")}</option><option value="light">{tr("Light", "Clair")}</option>'
            f'<option value="dark">{tr("Dark", "Sombre")}</option></select><button id="print" type="button" data-control disabled>'
            f'{tr("Print", "Imprimer")}</button></div></div><div class="title-block"><p class="eyebrow">{title}</p>'
            f'<h1>{escaped(info["title"])}</h1><p class="scope">{escaped(info["scope"])}</p></div>'
            f'<p class="privacy">{notice}</p><nav class="section-nav" aria-label="{tr("Report sections", "Sections du rapport")}">'
            f'<a href="#records">{tr("Records", "Entrées")}</a><a href="#coverage">{tr("Coverage", "Couverture")}</a>'
            f'<a href="#citations">Citations</a><a href="#relations">Relations</a></nav></header><main>'
            '<div class="stats">' + ''.join(stats_html) + '</div>'
            f'<noscript><p class="privacy">{tr("JavaScript is disabled. All records, including history, remain visible. Filters are unavailable.", "JavaScript est désactivé. Toutes les entrées, dont l’historique, restent visibles. Les filtres sont indisponibles.")}</p></noscript>'
            f'<section class="panel" id="records" aria-labelledby="records-heading"><div class="panel-heading"><h2 id="records-heading">'
            f'{tr("Evidence and observations", "Pièces et observations")}</h2><p>{tr("Search the recorded text, references and details. Filters apply only to this section.", "Rechercher dans les textes, références et détails enregistrés. Les filtres concernent uniquement cette section.")}</p></div>'
            f'<div class="filters"><label class="field search" for="search">{tr("Search this case", "Rechercher dans ce dossier")}'
            f'<input id="search" type="search" autocomplete="off" placeholder="{tr("Text, reference, tag…", "Texte, référence, étiquette…")}" data-control disabled></label>'
            f'<label class="field" for="kind">Type<select id="kind" data-control disabled><option value="">{tr("All types", "Tous les types")}</option>'
            + ''.join(f'<option value="{key}">{label}</option>' for key, label in kinds.items())
            + f'</select></label><label class="field" for="focus">{tr("Review focus", "Point de contrôle")}<select id="focus" data-control disabled>'
            f'<option value="">{tr("All records", "Toutes les entrées")}</option><option value="review">{tr("Needs review", "À réexaminer")}</option>'
            f'<option value="citation">{tr("Citation issues", "Citations à vérifier")}</option><option value="uncertain">{tr("Uncertain event times", "Horaires incertains")}</option>'
            f'</select></label><label class="check"><input type="checkbox" id="history" data-control disabled>{tr("Include history", "Inclure l’historique")}</label>'
            f'<button id="reset" type="button" data-control disabled>{tr("Reset", "Réinitialiser")}</button></div>'
            f'<div class="results-line"><output id="count" aria-live="polite" aria-atomic="true" data-label="{tr("records", "entrées")}">{len(entries)} {tr("records, including history", "entrées, historique inclus")}</output>'
            f'<span>{tr("Read-only snapshot", "Instantané en lecture seule")}</span></div><div class="scroll"><table class="records-table">'
            f'<thead><tr><th scope="col">ID</th><th scope="col">Type / {tr("Status", "État")}</th><th scope="col">Observation</th></tr></thead><tbody>'
            + ''.join(rows_html) + '</tbody></table></div>'
            f'<p id="empty" class="empty" hidden>{tr("No records match these filters. Reset them to return to the case.", "Aucune entrée ne correspond aux filtres. Les réinitialiser pour retrouver le dossier.")}</p></section>'
            f'<section class="panel" id="coverage" aria-labelledby="coverage-heading"><div class="panel-heading"><div class="heading-line">'
            f'<h2 id="coverage-heading">{tr("Declared research coverage", "Couverture déclarée des recherches")}</h2>'
            f'<span class="badge">{declared["completed_categories"]} / {declared["defined_categories"]} {tr("categories completed", "catégories terminées")}</span></div>'
            f'<p>{tr("Declared requirements only. A completed search does not prove absence or establish a conclusion. Partial searches remain visible.", "Questions déclarées uniquement. Une recherche terminée ne prouve ni une absence ni une conclusion. Les recherches partielles restent visibles.")}</p></div>'
            f'<div class="panel-body">{coverage_html}</div></section>'
            f'<section class="panel" id="citations" aria-labelledby="citations-heading"><div class="panel-heading"><h2 id="citations-heading">'
            f'{tr("Citation checks", "Contrôle des citations")}</h2><p>{tr("All recorded citations, including history. Checks compare locators and exact excerpts with registered bytes; they do not assess support for a claim.", "Toutes les citations enregistrées, historique inclus. Le contrôle compare les repères et extraits exacts aux octets enregistrés ; il ne valide pas leur appui à une conclusion.")}</p></div>'
            f'<div class="panel-body"><div class="citation-stats">{citation_stats}</div>{citation_html}</div></section>'
            f'<section class="panel" id="relations" aria-labelledby="relations-heading"><div class="panel-heading"><div class="heading-line">'
            f'<h2 id="relations-heading">Relations</h2><span class="badge">{len(nodes)} {tr("nodes", "nœuds")} · {len(edges)} {tr("links", "liens")}</span></div>'
            f'<p>{tr("Analyst-declared links, including claim history. Candidate links remain uncertain.", "Liens déclarés par l’analyste, historique des conclusions inclus. Les liens candidats restent incertains.")}</p></div>'
            f'<div class="panel-body"><details class="graph-detail"><summary>{tr("Open relation diagram", "Ouvrir le schéma des relations")}</summary><div class="scroll">'
            + graph_html + '</div></details>' + edge_list + '</div></section></main>'
            f'<footer class="page-footer"><p>{tr("OSINT Forge · Local review artifact · Original case files are unchanged by this view.", "OSINT Forge · Rapport de relecture local · Cette vue ne modifie pas les fichiers du dossier.")}</p>'
            f'<p class="screen-note">{tr("Print includes all records and history. Search and appearance choices stay in this page.", "L’impression inclut toutes les entrées et leur historique. Recherche et apparence restent dans cette page.")}</p>'
            f'<p class="print-note">{tr("Printed view includes all records and history, regardless of screen filters.", "La vue imprimée inclut toutes les entrées et leur historique, quels que soient les filtres à l’écran.")}</p></footer>'
            f'<script>{SCRIPT}</script></body></html>')
    data = page.encode()
    require(len(data) <= MAX_JSON, "REPORT_TOO_LARGE")
    return data
