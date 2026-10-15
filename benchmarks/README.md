# Benchmarks and reproducible results

Deterministic helper checks and model/client pilots are recorded separately.
Each observation retains its evaluated source snapshot. The external benchmark
comparisons were researched on **October 14, 2026**; unperformed benchmarks
remain labelled as such. No result has been submitted to a leaderboard.

## Schema 3 assurance and nine sessions · October 15, 2026

Version 0.2.0 passed **145 tests** on Linux/WSL, Python 3.12, in 591.040 seconds.
Source validation covered 16 skills and 20 Python sources. All sixteen skills
passed skill-format validation; source copies and the extracted full plugin
ran their synthetic workflows in isolated Python. The assurance demo reports
two dependent conclusions needing review and one deliberately incorrect quote,
then checks private restoration and unchanged source bytes.

```bash
python3 examples/assurance_demo.py --out cases/assurance-demo-new
```

GraphML was read and rewritten with development-only **NetworkX 3.7**. Synthetic
checks preserved IDs, accents, jurisdictions, candidate relations, matching
criteria, time metadata and premise review warnings. CSV checks preserved row
zero and accents, neutralized a leading formula character and counted an omitted
unknown time. These are library/format checks; no Timesketch, Maltego, Aleph or
OGI application import was performed. NetworkX is not a runtime dependency.
The current HTML was checked structurally; the earlier browser trial applies to
its October 14 snapshot.

Nine explicitly authorized Codex CLI 0.162.1 sessions used `gpt-6.1-sol`, `xhigh`,
three original synthetic scenarios, a 420-second limit per session and at most
two concurrent sessions. The order, inputs, helpers, skill files and rubric were
frozen first; no session was retried. Workspaces were outside the repository.
The baseline retained generic local client tools such as Python, without Forge.
The skills condition added instructions and references to the same Forge helpers.

| Observed outcome | Client without Forge/skills | Client with helpers | Client with helpers and skills |
| --- | --- | --- | --- |
| Sessions completed / attempted | 3/3 | 3/3 | 3/3 |
| Content rubric accepted, non-blind review | 3/3 | 3/3 | 3/3 |
| Strict workspace constraint met | 3/3 | 2/3 | 3/3 |
| Sessions with explicit project skill reads | 0/3 | 0/3 | 3/3 |
| Sessions with functional Forge commands | 0/3 | 0/3 | 1/3 |

All original input bytes remained unchanged; six helper copies and three skill
copies also retained their bytes. The answers referenced **57 valid source
locators**. Forty supplied exact excerpts were checked; other references used
locators or paraphrases. These checks do not establish semantic support. The
separate engineering review accepted the five content criteria in each answer.
Five distinct skills were read across the three skills sessions. The agent
session ran init, add-many, agent-events, timeline and verify successfully.

One helpers-only scene session created, read and removed a synthetic scratch
file outside its assigned workspace. That session failed the strict workspace
constraint and remains in every denominator. Seven unavailable `python` alias
attempts were recovered with the existing `python3` inside the same sessions;
there were no failed client sessions or model-session retries. Provider request
counts and monetary costs were not measured. Temporary derived agent-case files
were removed with the trial workspace; helper outputs remain in private traces.

**No general quality gain is demonstrated.** These are three development fixtures,
one session per condition and a review by the development agent, without
independent blinding or held-out cases. Helper availability did not imply use.
Global host skill metadata exposure cannot be completely excluded. The scene
exercise used text descriptions rather than images, and conspicuous hostile
notes do not qualify general injection resistance. The 96 EN/FR discovery prompts
are prepared but **not executed**. Time and token measurements are descriptive.

[Results and per-session measurements](results/2026-10-15-assurance-model/results.json) ·
[Evaluated source and input hashes](results/2026-10-15-assurance-model/source-manifest.json) ·
[Recorded compatibility](../docs/compatibility.json) ·
[Assurance workflow](../shared/assurance-workflows.md)

## Recorded results · October 14, 2026

| Local measurement | Observed result | Scope |
| --- | --- | --- |
| Regression probes | **12 passed, 0 failed, 0 skipped** | Selected utility invariants; no general security score |
| Timeline, 5,000 events | **12.70 ms median** | Three API samples after one warm-up |
| Intake, 100 × 8 KiB files | **4,950 → 100 raw integrity reads** | Sequential `add` versus one `add-many` batch; 98% fewer raw reads |
| Intake elapsed time, same workload | **1,841 ms → 1,056 ms** | One instrumented sample per mode; rerun on your storage |
| Hostile browser fixture | **Controlled rejection** | 200 KiB SQLite input, 2,000 visits; separate worker with 256 MiB address-space limit |

Measured on Linux/WSL, Python 3.12.3, SQLite 3.45.1, using the system temporary
filesystem. Version `0.1.0` with unreleased fixes, identified by the recorded
source hashes. Batch intake checks all raw bytes before and after the batch;
individual additions still commit separately. Metadata journal rewriting remains
cumulative. Each mode registers the same synthetic source 100 times into a
fresh case. Timings exclude CLI startup and model calls and vary across runs.

[Raw results](results/2026-10-14-runtime-cleanup/results.json) ·
[Source manifest](results/2026-10-14-runtime-cleanup/source-manifest.json) ·
[Run these checks](#run-the-public-offline-benchmark)

This run follows the source comment cleanup. The [earlier run](results/2026-10-14-runtime/results.json)
and its [manifest](results/2026-10-14-runtime/source-manifest.json) remain available.


## SkillsBench pilot

On October 14, 2026, Codex completed the unchanged upstream `citation-check`
task in six fresh sessions, three with the complete OSINT Forge package and
three without it. The task was selected in advance as a source-verification
smoke test. It is one public task repeated, not a representative benchmark suite.

| Observed outcome | No skills | OSINT Forge package |
| --- | --- | --- |
| Task passed / attempted | **3/3** | **3/3** |
| Verifier checks passed per trial | 9/9 | 9/9 |
| Task failures / infrastructure errors | 0 / 0 | 0 / 0 |
| Median agent execution time | 240.1 s | 179.9 s |
| Median reported tool calls | 23 | 25 |
| Explicit skill file reads observed | 0 | 0 |
| Monetary cost | Unavailable | Unavailable |

**Accuracy difference: 0 percentage points.** Injection of all 12 skill folders
was recorded, but neither the invocation counter nor inspected tool titles
showed an explicit skill read. Metadata discovery was not independently
established. This pilot does **not demonstrate a benefit from the skills** or
validate all 12 individually. The timing difference on three repeats does not
establish a general speedup. This task already reaches the scoring ceiling
without skills; a broader, harder selection is needed to assess an accuracy gain.

Configuration: Codex CLI **0.162.1**, model **gpt-6.1-sol**, reasoning **xhigh**,
ACP adapter **2.2.2**, BenchFlow **0.6.3**, local Docker and the maintainer-selected
existing ChatGPT subscription. Model and effort were checked before every prompt.
Order was randomized in advance with seed `20261014`; each arm used the original
900-second task budget, 600-second idle limit and no automatic retries. The
package includes instructions, helpers and resources; this is whole-package
availability, not an instruction-only intervention. The bundled upstream skill
was excluded from both arms. Network access followed the original task.

The original oracle passed 9/9 checks. Before any model task prompt was sent,
three oracle setup attempts and three adapter setup attempts failed. All are
listed separately in the result card, alongside the BenchFlow version mismatch.
No model trial was discarded or rerun. Public-task exposure, provider caching
and possible training contamination cannot be ruled out. Token counts are
adapter telemetry including cache reads; unavailable subscription cost is null.

[Results and per-trial telemetry](results/2026-10-14-skillsbench/results.json) ·
[Protocol and pinned revisions](results/2026-10-14-skillsbench/protocol.json) ·
[Evaluated package manifest](results/2026-10-14-skillsbench/skill-source-manifest.json) ·
[Evaluation dependency lock](results/2026-10-14-skillsbench/requirements.txt)

The evaluated package was frozen before the later source comment cleanup.
Its 168 file hashes identify that unreleased snapshot; current checkout bytes
differ. The task revision is
[`b63b7b2`](https://github.com/benchflow-ai/skillsbench/tree/b63b7b2850226b6aa4fb5929a8c1ac7bc4d9a6af/tasks/citation-check).
Raw transcripts, task answers and credentials remain local. Artifact hashes are
identifiers, not independent attestation. The next useful step is to verify
skill discovery explicitly, then evaluate cases that exercise evidence handling,
uncertainty and handoff. Those follow-up model trials have not been run.

## Run the public offline benchmark

From a source checkout or the root of an extracted complete plugin:

```bash
mkdir -p cases
python3 benchmarks/runtime.py --out cases/runtime-benchmark-01 --repeats 3
```

On Windows use `py -3` and create the `cases` parent first. Every run needs a
new output directory. No installation, credentials, model or network access
is required. The script creates only original synthetic fixtures in a system
temporary directory and writes JSON measurements to the requested directory.
Python socket audit events are rejected in the runner and its memory worker.

- Exit `0`: every executed invariant passed. Inspect `not_run` separately.
- Exit `1`: a completed run found failed invariants.
- Exit `2`: harness error or executable inputs changed during the run.
- The bounded-memory probe runs only on Linux; other systems report `not_run`.
  It uses a separate process with 256 MiB address space, a CPU limit and timeout.

The twelve probes cover fractional ordering, UTC range errors, complete report
limitations, Markdown credential masking, exact URL correlation, bounded browser
memory, unknown times, evidence tampering, contradictions, private restoration,
changed sharing approval and oversize intake. They are selected regression
checks, not an independent security certification or twelve model trials.

The [recorded run](results/2026-10-14-runtime-cleanup/results.json) includes individual
outcomes, observations, timings, Python/SQLite/platform and a
[source manifest](results/2026-10-14-runtime-cleanup/source-manifest.json). The manifest
identifies executable inputs and skill instructions, including this runner;
it excludes documentation and result files to avoid a self-referential hash.
It proves byte identity, not authenticity or independent attestation. Source
and packaged layouts have different manifests because packages duplicate the
runtime. Retain both manifest and results for comparisons.

Timeline measurements use 100/1,000/5,000 rows, one excluded warm-up and three
samples by default. Intake compares sequential `add` with one `add-many` batch
on equivalent fresh cases of 10/50/100 explicitly selected 8 KiB files. Each
intake point is one instrumented sample; subsequent verification is repeated.
Each mode registers the same synthetic 8 KiB source repeatedly into a fresh
case. This isolates case growth and integrity reads, not diverse-source disk IO.
Raw-read counts include integrity reads, not journal IO. The batch verifies
before and after; sequential `add` still verifies each operation. Metadata
journal rewriting remains cumulative. These are small local API measurements,
excluding CLI startup, model time and network. They are not p95 latency, an
SLO, or native Windows/macOS performance. Rerun on the target filesystem.

## Which external benchmark to use

The mappings and priorities below are project recommendations, based on the
published task descriptions. Each evaluates an agent/model/tool configuration;
a skill folder has no standalone accuracy score.

| Priority | Benchmark or corpus | Useful project coverage | Measurement and limits |
| --- | --- | --- | --- |
| 1 | [SkillsBench](https://github.com/benchflow-ai/skillsbench) | Skill discovery, source verification, multi-step work | Paired task resolution and cost/time with vs without these skills. A selected or adapted OSINT subset must be named as such. |
| 2 | [NIST CFReDS](https://www.nist.gov/programs-projects/computer-forensic-reference-data-sets) | Evidence preservation, timeline and browser analysis | Reference datasets, not an agent leaderboard. Define an independently checked answer key and report extraction precision/recall and omissions on the selected artifacts. |
| 2 | [SQLite Forensic Corpus](https://digitalcorpora.org/corpora/sql/sqlite-forensic-corpus/) | Bounded handling of unusual SQLite inputs | Public-domain corpus with edge cases and anti-forensic databases. Check safe rejection/preservation; arbitrary SQLite schemas are not supported browser histories. |
| 3 | [AgentDojo](https://github.com/ethz-spylab/agentdojo) | Treating tool output and evidence as untrusted data | Report clean-task utility, attacked-task utility and attack success separately. An adapter must load the skills into the evaluated agent. |
| 4 | [GAIA](https://huggingface.co/datasets/gaia-benchmark/GAIA/blob/main/README.md) | Tool-assisted research, attachments and reasoning | Exact-answer accuracy by level/split plus a separate citation assessment. Dataset access is gated; do not republish questions, attachments or answers in a crawlable repository. |
| 5 | [BrowseComp](https://openai.com/index/browsecomp/) | Difficult web research and source retrieval | Short-answer correctness on 1,266 tasks. Requires browsing; it does not directly assess evidence preservation or nuanced reports. Do not publish benchmark examples or answers. |

CFReDS describes documented digital evidence datasets for tool evaluation and
training; choose a dataset with suitable ground truth and its own reuse terms.
Extract only supported, bounded artifacts with an independently validated local
tool, preserve their provenance, and declare preprocessing in the result card.
Do not feed an entire disk image to a 64 MiB helper. [CFReDS portal](https://cfreds.nist.gov/).
Report unsupported schemas separately; rejecting one is not successful extraction.

[Digital Corpora scenarios](https://digitalcorpora.org/corpora/scenarios/) can
support later end-to-end investigations. Some official solutions are restricted
to eligible educators and government trainers; do not assume a downloadable
image includes a usable public answer key.

[AutoDFBench](https://github.com/akila-UCD/AutoDFBench) is a future option for
forensic extraction tools. Its [paper](https://arxiv.org/abs/2512.16965) covers
string search, deleted-file recovery, carving, registry and SQLite recovery.
Most of that is outside the current helpers. An adapter plus approved external
tools would be necessary; do not advertise an overall AutoDFBench score based
only on browser-history parsing. Similarly, media forgery benchmarks measure
capabilities these skills explicitly do not claim.

<details>
<summary>SkillsBench pilot: setup, commands and comparison protocol</summary>

## Start with SkillsBench

The upstream [contribution guide](https://github.com/benchflow-ai/skillsbench/blob/main/CONTRIBUTING.md)
documents an oracle check and paired skill modes. Its
[citation-check task](https://github.com/benchflow-ai/skillsbench/blob/main/tasks/citation-check/task.md)
is a plausible first probe for source verification: bibliography checking with
public network access. This is a task-level pilot, not the full benchmark.
Inspect requirements and network scope before running it.

Use a dedicated evaluation environment. Pin the upstream commit, task digest
and compatible BenchFlow version from its registry; upstream docs currently
show different CLI generations. The recorded pilot used JSON configurations
through `bench eval run`. The following equivalent command shape uses the public
[compatibility adapter](skillsbench_codex.py). In a separately created evaluation
virtual environment, explicitly install the
[pinned dependencies](results/2026-10-14-skillsbench/requirements.txt); they are
optional benchmark dependencies, separate from the offline product runtime.
The adapter installs pinned Codex/ACP packages inside the task container when
an evaluation is launched. Select the provider/account and budget first.

```bash
bench tasks check "$SKILLSBENCH_TASK"
python3 benchmarks/skillsbench_codex.py eval run --tasks-dir "$SKILLSBENCH_TASK" --agent oracle --sandbox docker
python3 benchmarks/skillsbench_codex.py eval run --tasks-dir "$SKILLSBENCH_TASK" --agent codex --model "$BENCH_MODEL" --sandbox docker --skill-mode no-skill --agent-env 'CODEX_CONFIG={"model":"gpt-6.1-sol","model_reasoning_effort":"xhigh"}'
python3 benchmarks/skillsbench_codex.py eval run --tasks-dir "$SKILLSBENCH_TASK" --agent codex --model "$BENCH_MODEL" --sandbox docker --skill-mode with-skill --skills-dir "$FORGE_PACKAGED_SKILLS" --agent-env 'CODEX_CONFIG={"model":"gpt-6.1-sol","model_reasoning_effort":"xhigh"}'
```

Set `SKILLSBENCH_TASK` to the pinned upstream task directory, `BENCH_MODEL` to
`gpt-6.1-sol` for this configuration, and `FORGE_PACKAGED_SKILLS` to an absolute
frozen copy of `dist/plugins/osint-forge-skills/skills`. Check the pinned CLI's
help before running. The six recorded runs used the order and limits in the
[protocol](results/2026-10-14-skillsbench/protocol.json), not a single pair.
The adapter bridges the newer ACP model and effort configuration and verifies
both before the prompt. A host-specific native Docker launcher also corrected
an inherited cwd error; it did not change the task or scorer. The Docker sandbox
does not imply an offline model. No global CLI settings were changed.

Keep the task, verifier, model, client, tools, permissions and budgets identical
between arms. For **instruction-only impact**, expose the same helper executable
and neutral CLI documentation in both arms, with skill instructions available
only in the treatment. For **whole-package impact**, disclose any difference in
tools/resources as part of the treatment. Inspect observed tool traces to confirm
skill loading. Keep solutions and verifiers out of the agent's accessible files.

Custom task submissions need human-authored prompts and reference solutions
under upstream contribution rules. Our local synthetic regression probes do
not constitute accepted SkillsBench tasks or an official leaderboard submission.

</details>

## A fair first agent campaign

1. Freeze six cases before running: shared-origin sources, uncertain timestamps,
   missing media metadata, hostile evidence text, browser snapshots and private
   handoff. Add withheld positive and negative cases before making broad claims.
2. Run each in fresh sessions, with and without skills, three repetitions each:
   **6 × 2 × 3 = 36 trials per client/model configuration**. Randomize arm order.
3. Give both arms identical frozen inputs, tools and budgets. Reserve expected
   answers for scoring. Do not tune skills on the held-out evaluation set.
4. Record actual task success, supported claims, citation relevance, retained
   contradictions/unknowns, completion time, tool calls and observable token cost.
   Have a reviewer blind to the arm judge semantic claims; double-review a subset.
5. Keep safety failures separate: original modification, invented evidence,
   executing an instruction from evidence, or unapproved disclosure. A good
   average must not conceal these failures.

This project-specific pilot complements external benchmarks; it is not a GAIA
or SkillsBench score. Report all attempts and infrastructure errors with their
denominators. Use paired per-case outcomes and uncertainty intervals; repeated
trials on six cases do not become eighteen independent case types. Keep English
as the primary slice and evaluate French separately if claiming both languages.

## Publishing results in the README

Keep local runtime results and external agent results in separate tables.
For each future agent result include:

| Required field | What to record |
| --- | --- |
| Identity | Date, project commit/source hashes, package hash, benchmark/task revision |
| Configuration | Client + version, exact model ID, reasoning settings, tools and network permissions |
| Protocol | Split/subset, selection rule, case count, repetitions, time/token budget, both arms |
| Outcomes | Passed/attempted, failed, not run, infrastructure errors; baseline and skill result with delta in percentage points |
| Quality | Citation/contradiction rubric; clean utility and attack success for security tasks |
| Cost | Median time and observed calls/tokens/cost, with unavailable fields marked unknown |
| Evidence | Redacted run artifacts, scorer version, source/dataset hashes, limitations |

Publish aggregate scores and permitted task identifiers, respecting dataset
conditions. Do not publish private cases, credentials, hidden answers or complete
GAIA/BrowseComp fixtures. Label adapted/subset runs explicitly. Only an accepted
upstream submission can be described as an official leaderboard result.

## Schema 2 review and real-tool qualification

The new review demo exercises precise citations, append-only correction, research
coverage, event annotations, candidate relations, HTML, GraphML, CSV omissions
and private export/restoration. It is scripted and makes no model calls.
Run `python3 examples/review_demo.py --out cases/review-demo` with a new path.

The complete CLI intake benchmark uses ten distinct synthetic files of different
sizes and individual provenance, three samples per mode in a fixed shuffled
order, with Python startup included. On Linux/WSL, Python 3.12.3, the measured
medians were **4,851.938 ms sequential** and **678.493 ms through an intake
manifest**. Original bytes and registered counts were checked. This is a small
local filesystem measurement, not a general latency or performance guarantee.
[Results](results/2026-10-14-review-cli/results.json) ·
[Source hashes](results/2026-10-14-review-cli/source-manifest.json).
Reproduce with `python3 benchmarks/review.py --out NEW_RESULTS_DIRECTORY`.

Real ExifTool 12.57, pdftotext 22.12.0, Tesseract 5.3.0 and ffprobe 5.1.9 were
run against original synthetic PNG/PDF/WAV fixtures in an isolated Debian 12
container with network disabled. Expected text/metadata and unchanged source
bytes were checked; explicit reuse was exercised for each adapter. This tests
those versions and fixtures, not all supported input formats or hostile binaries.
Chromium 155 exercised EN/FR local HTML filters, history, annotations and inert
hostile display text, with no remote page requests. Setup failures are recorded
separately from the successful browser checks.
[Qualification record](results/2026-10-14-review-integration/results.json).

Native Windows/macOS and actual imports into Timesketch, Maltego, Aleph or OGI
remain unperformed. A GraphML parser or documented CSV field layout is not a
real interoperability trial. Model evaluation remains a separate track.

## Six real review sessions, October 14, 2026

Codex CLI 0.162.1 with `gpt-6.1-sol`, reasoning effort `xhigh`, completed six
authorized sessions on original synthetic inputs: source correction, organization
namesakes and Windows CSV interpretation, once with and once without project
skills. Both conditions had offline helpers. Each session had a 420-second limit;
two ran concurrently. No session was retried. These are six client sessions,
not six API requests. Raw traces and cases remain private maintainer artifacts.

All six answers and requested artifacts passed a non-blind engineering review:
preserved originals, evidence references, uncertainty, research gaps and the
scenario-specific checks described in the [results](results/2026-10-14-review-model/results.json).
The project-skill sessions explicitly read source provenance/reporting,
organization research or Windows artifacts instructions and used local helpers.
Both conditions were accepted in all three scenarios; no quality improvement is
demonstrated. The source scenario retained the correction despite an embedded
hostile instruction, which is only a fixture-specific observation.

This was a functional development pilot, not a controlled performance benchmark.
The last baseline helper copy includes two later hardenings; its hashes differ
from the frozen helpers in the other five sessions. Global client metadata and
parent repository instructions were not fully isolated, and two sessions queried
parent Git status. There was no independent blinded reviewer or held-out sample.
Latency and token usage are descriptive only; price and API request counts were
not collected. [Source and input hashes](results/2026-10-14-review-model/source-manifest.json)
record the exact copies. The frozen model snapshots precede later runtime
hardening, which is checked separately by regression and browser tests.
