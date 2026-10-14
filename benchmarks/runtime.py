#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import platform
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'shared'
if not (RUNTIME / 'forgekit').is_dir():
    RUNTIME = ROOT / 'skills/of-case-start/scripts'
sys.path.insert(0, str(RUNTIME))
from forgekit import VERSION
from forgekit import casefiles
from forgekit.analysis import browser, save_analysis, timeline
from forgekit.casefiles import add_claim, add_evidence, add_many, initialize, verify
from forgekit.cli import correlate, main as cli_main
from forgekit.reporting import export_case, prepare_share, render_report, restore_case
from forgekit.safeio import ForgeError, MAX_FILE, digest, json_bytes


def no_network(event, args):
    if event.startswith('socket.'):
        raise RuntimeError('BENCHMARK_NETWORK_FORBIDDEN')


sys.addaudithook(no_network)


def source_manifest():
    paths = set((RUNTIME / 'forgekit').glob('*.py'))
    paths.update((ROOT / 'skills').rglob('*.md'))
    paths.update((ROOT / 'skills').rglob('*.yaml'))
    paths.update((ROOT / 'skills').rglob('*.py'))
    paths.update(ROOT / name for name in ('VERSION', 'plugin.json',
                                        'shared/case-contract.md', 'benchmarks/runtime.py'))
    return {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in sorted(paths)}


def new_case(base, label='probe', scope='Original synthetic fixtures; offline only'):
    case = base / label
    initialize(case, 'Synthetic benchmark', scope)
    return case


def intake(base, case, content, name='input.dat'):
    source = base / name
    source.write_bytes(content)
    return add_evidence(case, source)


def history(path, urls, visits):
    with sqlite3.connect(path) as connection:
        connection.executescript('CREATE TABLE urls(id INTEGER PRIMARY KEY,url TEXT,title TEXT);'
                                 'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER,visit_time INTEGER);')
        connection.executemany('INSERT INTO urls VALUES (?, ?, ?)',
                               [(i, url, 'Synthetic') for i, url in enumerate(urls, 1)])
        connection.executemany('INSERT INTO visits VALUES (?, ?, ?)', visits)


def fractional_order(base):
    case = new_case(base)
    row = intake(base, case, json_bytes([
        {'timestamp': '2026-10-01T08:00:00Z', 'event': 'First'},
        {'timestamp': '2026-10-01T08:00:00.100000Z', 'event': 'Second'}]))
    result = timeline(case, row['id'], 'json')
    order = [item['record_index'] for item in result['events']]
    return order == [0, 1], {'expected_record_order': [0, 1], 'actual_record_order': order}


def extreme_time(base):
    case = new_case(base)
    row = intake(base, case, json_bytes([
        {'timestamp': '0001-01-01T00:00:00+01:00', 'event': 'Unrepresentable UTC'},
        {'timestamp': '2026-10-01T08:00:00Z', 'event': 'Ordinary event'}]))
    output = case / 'analysis/timeline.json'
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        code = cli_main(['timeline', '--case', str(case), '--evidence', row['id'], '--out', str(output)])
    states = []
    if code == 0:
        states = sorted(item['time_status'] for item in json.loads(output.read_text())['events'])
    return code == 0 and states == ['invalid', 'normalized'], {
        'expected': 'retain invalid time and ordinary event', 'exit_code': code,
        'actual_time_states': states, 'response': json.loads(captured.getvalue())}


def report_limits(base):
    marker = 'SYNTHETIC CRITICAL LIMITATION AT END'
    case = new_case(base, scope='A' * 4500 + marker)
    row = intake(base, case, b'Synthetic evidence')
    add_claim(case, 'Synthetic observation', [row['id']], [], 'observed', 'medium', 'B' * 4500 + marker)
    retained = render_report(case).decode().count(marker)
    return retained == 2, {'expected_tail_markers': 2, 'retained_tail_markers': retained,
                           'scope_and_rationale_characters': 4500 + len(marker)}


def markdown_mask(base):
    case = new_case(base)
    row = intake(base, case, b'Synthetic evidence')
    text = 'api_key=SYNTHETICVALUEONLY'
    add_claim(case, 'Synthetic credential rendering', [row['id']], [], 'observed', 'low', text)
    raw, raw_view = base / 'raw-text.md', base / 'raw-view.md'
    raw.write_text(text)
    raw_result = prepare_share(raw, raw_view)
    report, view = case / 'reports/report.en.md', base / 'view.md'
    report.write_bytes(render_report(case))
    result = prepare_share(report, view)
    retained = 'SYNTHETICVALUEONLY' in view.read_text()
    control = 'SYNTHETICVALUEONLY' not in raw_view.read_text()
    return control and not retained, {'raw_text_control_masked': control,
        'raw_credential_masks': raw_result['automatic_masks']['credentials'],
        'rendered_credential_masks': result['automatic_masks']['credentials'],
        'synthetic_value_retained_in_review_view': retained, 'public_export_performed': False}


def distinct_urls(base):
    case = new_case(base)
    paths, values = [], []
    for index in range(2):
        source = base / f'history-{index}.sqlite'
        url = 'https://fixture.invalid/' + 'a' * 2100 + str(index)
        values.append(url)
        history(source, [url], [(1, 1, (index + 1) * 1000000)])
        row = add_evidence(case, source)
        result = browser(case, row['id'])
        result['input'] = {'evidence_id': row['id'], 'sha256': row['sha256']}
        output = case / 'analysis' / f'browser-{index}.json'
        save_analysis(case, output, result)
        paths.append(str(output))
    links = correlate(str(case), paths)['candidate_links']
    false_matches = sum(row['basis'] == 'same_url' for row in links)
    return false_matches == 0, {'original_urls_different': values[0] != values[1],
        'original_url_length': len(values[0]), 'false_same_url_links': false_matches}


def memory_worker():
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (10, 12))
    with tempfile.TemporaryDirectory(prefix='forge-bench-memory-') as temporary:
        base = Path(temporary)
        case = new_case(base)
        source = base / 'history.sqlite'
        history(source, ['https://fixture.invalid/' + 'a' * (160 * 1024)],
                [(i, 1, i * 1000000) for i in range(1, 2001)])
        row = add_evidence(case, source)
        captured = io.StringIO()
        try:
            with contextlib.redirect_stdout(captured):
                code = cli_main(['browser', '--case', str(case), '--evidence', row['id'],
                                 '--out', str(case / 'analysis/browser.json')])
            response = json.loads(captured.getvalue())
            bounded = code == 2 and response.get('code') in {
                'SQLITE_ANALYSIS_FAILED', 'BROWSER_FIELD_TOO_LARGE', 'ANALYSIS_OUTPUT_TOO_LARGE'}
            bounded = bounded and not (case / 'analysis/browser.json').exists()
            result = {'bounded_cli_outcome': bounded, 'exit_code': code, 'response': response}
        except MemoryError:
            result = {'bounded_cli_outcome': False, 'exception': 'unhandled_MemoryError'}
        result.update({'input_bytes': source.stat().st_size, 'visits': 2000,
                       'address_space_limit_mib': 256,
                       'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
        print(json.dumps(result))


def bounded_browser(base):
    if sys.platform != 'linux':
        return None, {'reason': 'Linux address-space containment not available; not run'}
    result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--memory-worker'],
                            cwd=ROOT, capture_output=True, text=True, timeout=20)
    if result.returncode:
        return False, {'worker_exit_code': result.returncode, 'bounded_worker': True}
    value = json.loads(result.stdout)
    return value['bounded_cli_outcome'], value


def uncertain_times(base):
    case = new_case(base)
    row = intake(base, case, json_bytes([
        {'timestamp': '2026-10-25T02:30:00', 'event': 'Missing offset'},
        {'timestamp': None, 'event': 'Missing time'}]))
    events = timeline(case, row['id'], 'json')['events']
    states = [item['time_status'] for item in events]
    return states == ['timezone_unknown', 'missing'] and all(e['utc'] is None for e in events), {'time_states': states}


def rejected(function, expected_code):
    try:
        function()
    except ForgeError as exc:
        return str(exc) == expected_code, {'expected_code': expected_code, 'actual_code': str(exc)}
    return False, {'expected_code': expected_code, 'actual_code': 'accepted'}


def tampered_bytes(base):
    case = new_case(base)
    row = intake(base, case, b'Synthetic original')
    (case / 'raw' / (row['id'] + '.bin')).write_bytes(b'Synthetic altered copy')
    return rejected(lambda: verify(case), 'EVIDENCE_INTEGRITY_MISMATCH')


def contradiction_gate(base):
    case = new_case(base)
    supporting = intake(base, case, b'Synthetic supporting text', 'support.txt')
    against = intake(base, case, b'Synthetic contradicting text', 'against.txt')
    return rejected(lambda: add_claim(case, 'Synthetic claim', [supporting['id']], [against['id']],
                                     'inferred', 'high', 'Unresolved contradiction'), 'UNRESOLVED_CONTRADICTION')


def private_roundtrip(base):
    case = new_case(base)
    row = intake(base, case, b'Synthetic original')
    add_claim(case, 'Synthetic claim', [row['id']], [], 'observed', 'medium', 'Literal text only')
    archive, resumed = base / 'private.zip', base / 'resumed'
    export_case(case, archive, 'private')
    restore_case(archive, resumed)
    names = ['case.json', 'evidence.jsonl', 'claims.jsonl', 'raw/' + row['id'] + '.bin']
    preserved = all((case / name).read_bytes() == (resumed / name).read_bytes() for name in names)
    return preserved and verify(resumed)['evidence_count'] == 1, {'member_bytes_preserved': preserved}


def changed_approval(base):
    case = new_case(base)
    view = base / 'reviewed.md'
    view.write_bytes(b'Synthetic original reviewed view')
    approved = digest(view.read_bytes())
    view.write_bytes(b'Synthetic altered view')
    passed, details = rejected(lambda: export_case(case, base / 'public.zip', 'public', view, approved),
                               'APPROVAL_DIGEST_MISMATCH')
    details['archive_created'] = (base / 'public.zip').exists()
    return passed and not details['archive_created'], details


def oversize_file(base):
    case = new_case(base)
    source = base / 'sparse.bin'
    with source.open('wb') as handle:
        handle.truncate(MAX_FILE + 1)
    return rejected(lambda: add_evidence(case, source), 'FILE_TOO_LARGE')


PROBES = [
    ('T01', 'Mixed fractional timestamps stay chronological', fractional_order),
    ('T02', 'Unrepresentable UTC remains an invalid row', extreme_time),
    ('R01', 'Accepted scope and rationale survive report rendering', report_limits),
    ('S01', 'Known credential masking survives Markdown rendering', markdown_mask),
    ('B01', 'Different full URLs do not become exact URL matches', distinct_urls),
    ('B02', 'Browser analysis handles a bounded memory budget', bounded_browser),
    ('C01', 'Missing time and timezone stay unknown', uncertain_times),
    ('C02', 'Evidence modification is rejected', tampered_bytes),
    ('C03', 'Unresolved contradictions block high confidence', contradiction_gate),
    ('C04', 'Private handoff preserves original bytes and records', private_roundtrip),
    ('C05', 'Changed sharing view rejects the previous digest', changed_approval),
    ('C06', 'Oversize files are rejected before intake', oversize_file),
]


def measured(function, repeats):
    function()
    samples = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        function()
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
    return {'unit': 'ms', 'samples': samples, 'median': statistics.median(samples),
            'min': min(samples), 'max': max(samples), 'warmup_runs': 1}


def performance(base, repeats):
    results = []
    for count in (100, 1000, 5000):
        workspace = base / f'events-{count}'
        workspace.mkdir()
        case = new_case(workspace)
        start = datetime(2026, 10, 1, tzinfo=timezone.utc)
        content = json_bytes([{'timestamp': (start + timedelta(seconds=i)).isoformat(),
                               'event': f'Synthetic event {i}'} for i in range(count)])
        row = intake(workspace, case, content)
        def run_timeline():
            result = timeline(case, row['id'], 'json')
            if result['event_count'] != count:
                raise RuntimeError('BENCHMARK_WRONG_EVENT_COUNT')
        results.append({'workload': 'timeline', 'events': count, 'input_bytes': len(content),
                        'fixture_sha256': digest(content), **measured(run_timeline, repeats)})
    for mode in ('sequential', 'batch'):
        for count in (10, 50, 100):
            workspace = base / f'{mode}-intake-{count}'
            workspace.mkdir()
            case = new_case(workspace)
            content = b'S' * 8192
            source = workspace / 'synthetic.bin'
            source.write_bytes(content)
            original_read = casefiles.read_bytes
            counter = {'raw_reads': 0, 'raw_bytes_read': 0}
            def counted_read(path, *args, **kwargs):
                data = original_read(path, *args, **kwargs)
                if Path(path).parent == case / 'raw':
                    counter['raw_reads'] += 1
                    counter['raw_bytes_read'] += len(data)
                return data
            started = time.perf_counter_ns()
            with patch.object(casefiles, 'read_bytes', counted_read):
                if mode == 'sequential':
                    for _ in range(count):
                        add_evidence(case, source)
                else:
                    add_many(case, [source] * count)
            elapsed = (time.perf_counter_ns() - started) / 1_000_000
            results.append({'workload': mode + '_intake', 'evidence_files': count,
                            'file_bytes': len(content), 'fixture_sha256': digest(content),
                            'elapsed_ms': elapsed, 'samples_count': 1,
                            'read_instrumentation': True, **counter,
                            'rehash_bytes_per_final_case_byte': counter['raw_bytes_read'] / (len(content) * count),
                            'verify': measured(lambda: verify(case), repeats)})
    return results


def run(output, repeats):
    if not output.parent.is_dir():
        raise ValueError('OUTPUT_PARENT_REQUIRED')
    output.mkdir()
    before = source_manifest()
    captured_at = datetime.now(timezone.utc).isoformat()
    outcomes = []
    with tempfile.TemporaryDirectory(prefix='forge-audit-benchmark-') as temporary:
        base = Path(temporary)
        for identifier, title, function in PROBES:
            workspace = base / identifier
            workspace.mkdir()
            started = time.perf_counter_ns()
            try:
                passed, observation = function(workspace)
                status = 'not_run' if passed is None else 'passed' if passed else 'failed'
            except Exception as exc:
                status, observation = 'harness_error', {'exception_type': type(exc).__name__}
            outcomes.append({'id': identifier, 'invariant': title, 'status': status,
                             'elapsed_ms': (time.perf_counter_ns() - started) / 1_000_000,
                             'observed': observation})
            print(json.dumps({'id': identifier, 'status': status}), flush=True)
        timings = performance(base, repeats)
    stable = before == source_manifest()
    result = {'schema_version': 1, 'benchmark_version': '1.1', 'executed_at_utc': captured_at,
              'tool_version': VERSION, 'source_manifest_sha256': digest(json_bytes(before)),
              'sources_unchanged': stable, 'python': platform.python_version(),
              'platform': platform.platform(), 'sqlite': sqlite3.sqlite_version,
              'machine': platform.machine(), 'fixture_storage': 'system_temporary_directory',
              'network_policy': 'Python socket audit events forbidden in runner and worker',
              'scope': 'selected synthetic utility invariants; not a model or general security score',
              'model_trials': 'not_run', 'probes': outcomes, 'performance': timings,
              'counts': {state: sum(row['status'] == state for row in outcomes)
                         for state in ('passed', 'failed', 'not_run', 'harness_error')}}
    (output / 'source-manifest.json').write_bytes(json_bytes(before))
    (output / 'results.json').write_bytes(json_bytes(result))
    print(json.dumps({'result': str(output / 'results.json'), 'counts': result['counts'],
                      'sources_unchanged': stable}), flush=True)
    if not stable or result['counts']['harness_error']:
        return 2
    return int(bool(result['counts']['failed']))


def main():
    parser = argparse.ArgumentParser(description='Offline synthetic regression probes and small-scale runtime measurements.\n\nExit 1 means a completed run found failed invariants; 2 means a harness error.\nThis measures utilities, not investigation-model quality. Use synthetic data only.\n')
    parser.add_argument('--out', type=Path, help='New local result directory; parent must exist')
    parser.add_argument('--repeats', type=int, default=3, choices=range(1, 11))
    parser.add_argument('--memory-worker', action='store_true', help=argparse.SUPPRESS)
    arguments = parser.parse_args()
    if arguments.memory_worker:
        memory_worker()
        return 0
    if arguments.out is None:
        parser.error('--out is required')
    try:
        return run(arguments.out, arguments.repeats)
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({'status': 'harness_error', 'exception_type': type(exc).__name__}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
