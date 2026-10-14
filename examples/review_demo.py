from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(ROOT / "skills/of-case-start/scripts"))
from forgekit.analysis import save_analysis
from forgekit.casefiles import add_claim, add_evidence, initialize, verify
from forgekit.exchange import compare_text, graphml, import_events, timesketch_csv
from forgekit.reporting import export_case, render_report, restore_case
from forgekit.review import append_review, intake_manifest
from forgekit.safeio import atomic_write, digest, json_bytes, read_bytes, require, safe_path
from forgekit.viewer import render_html


def demo(destination):
    output = safe_path(destination, exists=False)
    require(not output.exists(), "OUTPUT_EXISTS")
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    output.mkdir(mode=0o700)
    inputs = output / "inputs"
    inputs.mkdir(mode=0o700)
    (inputs / "notice-before.txt").write_text('Harbor Example Ltd\nOpening planned for 09:00.\n', encoding='utf-8')
    (inputs / "notice-after.txt").write_text('Harbor Example Ltd\nOpening postponed pending inspection.\n', encoding='utf-8')
    (inputs / "events.csv").write_text('TimeCreated,Description,EventId\n2026-10-01T09:00:00,Planned opening,10\n2026-10-01T09:30:00Z,Postponement notice published,11\n', encoding='utf-8')
    manifest = {'files':[
        {'path':'notice-before.txt','source_url':'https://bulletin.invalid/before','origin_group':'bulletin'},
        {'path':'notice-after.txt','source_url':'https://bulletin.invalid/after','origin_group':'bulletin'},
        {'path':'events.csv','origin_group':'synthetic-export'}]}
    atomic_write(inputs/'selected.json',json_bytes(manifest))
    case = output/'case'
    initialize(case, 'Harbor revision review', 'Original synthetic evidence only; no network research')
    intake_manifest(case, inputs/'selected.json')
    add_claim(case, 'An opening was planned; implementation is unknown.', ['E000001'], [], 'observed','low',
              'The notice is a plan, not an execution log.',
              citations=[{'evidence_id':'E000001','kind':'line','start':2,'end':2}])
    add_claim(case, 'The later supplied notice postpones the opening.', ['E000002'], [], 'observed','medium',
              'The supplied order is operator context, not independently verified publication chronology.',
              citations=[{'evidence_id':'E000002','kind':'line','start':2,'end':2}], supersedes='C000001')
    append_review(case, {'kind':'research','question':'Was the opening implemented?',
                        'query':'Supplied notices and event export','scope':'Synthetic October extracts',
                        'tool':'manual review','status':'partial','evidence':['E000001','E000002'],
                        'rationale':'No execution log is supplied.'})
    for label in ('Harbor Example Ltd','Dock Example Authority'):
        append_review(case, {'kind':'entity','entity_type':'organization','label':label,
                            'evidence':['E000001'],'rationale':'Synthetic example entity; association not established.'})
    append_review(case, {'kind':'relation','source':'R000002','target':'R000003','label':'possible operator',
                        'state':'candidate','evidence':['E000001'],'rationale':'Needs a registry filing.'})
    result = import_events(case,'E000003','TimeCreated','Description')
    save_analysis(case,case/'analysis/events.json',result)
    append_review(case, {'kind':'annotation','analysis':'analysis/events.json',
                        'sha256':digest(read_bytes(case/'analysis/events.json')),'record_index':0,
                        'tags':['timezone_unknown'],'note':'No UTC offset supplied',
                        'rationale':'Do not interpret the planned time as 09:00 UTC.'})
    save_analysis(case,case/'analysis/changes.json',compare_text(case,'E000001','E000002'))
    atomic_write(case/'analysis/relations.graphml',graphml(case))
    exported, losses = timesketch_csv(case,'analysis/events.json')
    atomic_write(case/'analysis/timesketch.csv',exported)
    atomic_write(case/'analysis/exchange-losses.json',json_bytes(losses))
    for language in ('en','fr'):
        atomic_write(case/f'reports/report.{language}.md',render_report(case,language))
        atomic_write(case/f'reports/report.{language}.html',render_html(case,language,['analysis/events.json']))
    export_case(case,case/'exports/private.zip','private')
    restore_case(case/'exports/private.zip',output/'restored')
    return {'status':'passed','case':str(case),'verification':verify(case),
            'exchange':losses,'network_calls':False,'model_calls':False}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='Create an original synthetic schema v2 review and exchange case.')
    parser.add_argument('--out',required=True)
    print(json.dumps(demo(parser.parse_args().out),sort_keys=True))
