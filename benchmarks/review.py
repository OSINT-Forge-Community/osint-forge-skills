from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/forge.py"
if not CLI.exists():
    CLI = ROOT / "skills/of-case-start/scripts/forge.py"


def call(*arguments):
    result = subprocess.run([sys.executable, "-B", str(CLI), *map(str, arguments)],
                            capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError("BENCHMARK_COMMAND_FAILED")
    return json.loads(result.stdout)


def run(destination):
    output = Path(destination)
    output.mkdir(parents=True, exist_ok=False)
    samples = {"sequential": [], "manifest": []}
    order = [mode for _ in range(3) for mode in samples]
    random.Random(20261014).shuffle(order)
    with tempfile.TemporaryDirectory(prefix="forge-review-bench-") as temporary:
        base = Path(temporary)
        files = []
        for index in range(10):
            path = base / f"source-{index}.txt"
            path.write_bytes((f"Synthetic document {index}\n".encode() * ((index + 1) * 150)))
            files.append({"path":path.name,"source_url":f"https://source{index}.invalid/notice",
                          "origin_group":f"origin-{index}"})
        originals = {item['path']:hashlib.sha256((base/item['path']).read_bytes()).hexdigest() for item in files}
        manifest = base / "intake.json"
        manifest.write_text(json.dumps({"files": files}))
        for index, mode in enumerate(order):
            case = base / f"case-{index}"
            call("init", "--case", case, "--title", "Synthetic CLI benchmark", "--scope", "Selected synthetic files only")
            started = time.perf_counter()
            if mode == "manifest":
                call("intake", "--case", case, "--manifest", manifest)
            else:
                for item in files:
                    call("add", "--case", case, "--source", base/item['path'],
                         "--url", item['source_url'], "--origin-group", item['origin_group'])
            samples[mode].append(round((time.perf_counter() - started) * 1000, 3))
            assert call("verify", "--case", case)["evidence_count"] == 10
        assert originals == {name:hashlib.sha256((base/name).read_bytes()).hexdigest() for name in originals}
    result = {"status":"passed", "python":sys.version.split()[0], "platform":sys.platform,
              "files":10, "repetitions_per_mode":3, "order":order,
              "samples_ms":samples, "median_ms":{key:statistics.median(values) for key,values in samples.items()},
              "originals_unchanged":True, "network_calls":False,"model_calls":False,
              "scope":"End-to-end CLI intake of 10 distinct synthetic text files with per-file provenance, on the host temporary filesystem; includes Python startup. No general speedup or native Windows/macOS claim."}
    source_paths = list((ROOT/'shared/forgekit').glob('*.py')) if (ROOT/'shared/forgekit').is_dir() else list((CLI.parent/'forgekit').glob('*.py'))
    source_paths += [CLI, Path(__file__)]
    manifest = {str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths}
    (output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    (output/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Measure complete CLI intake on distinct original synthetic files.')
    parser.add_argument('--out',required=True)
    print(json.dumps(run(parser.parse_args().out),sort_keys=True))
