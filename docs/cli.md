# Command reference

This reference describes helper version **0.3.0**. The [contract v4](../shared/case-contract.md)
defines invariants; [data formats](formats.md) describes the records.
From source, prefix commands with `python3 scripts/forge.py`; on PowerShell,
use `py -3 scripts/forge.py`. In a package, run a complete skill's
`scripts/forge.py`.

```text
python3 scripts/forge.py --help
python3 scripts/forge.py timeline --help
python3 scripts/forge.py --version
```

Relative paths resolve from the shell's current directory, not the skill
folder. Quote paths and text. Destination parents must exist. The
[quick start](demarrage.md) provides a walkthrough with runnable commands.

## Results and errors

A successful operation returns JSON on standard output with exit status **0**.
A controlled error returns status **2**, for example:

```json
{"status": "error", "code": "OUTPUT_EXISTS"}
```

Errors use fixed codes and do not echo the affected evidence. Successful
results can contain private metadata: apply the case's data policy.
`--help` and `--version` return text. In PowerShell, read `$LASTEXITCODE`
immediately after the command; in Bash, read `$?`.
[Troubleshooting](depannage.md) maps codes to actions.

## Optional local tools

`tools` discovers ExifTool, ffprobe, Poppler `pdftotext` and Tesseract on absolute
PATH entries, excluding the current directory. It executes and installs nothing.
`found_unverified` is a discovery result, not permission or compatibility proof.
`doctor` describes built-in parsers; its unsupported-format list does not test
the optional executables. Use `tools` for discovery and a selected synthetic
case for an actual executable trial.

```text
python3 scripts/forge.py tools
python3 scripts/forge.py tool-run --case CASE --evidence E000001 --tool exiftool --executable /absolute/path/to/exiftool --out CASE/analysis/metadata.json
```

`tool-run` requires `--case`, `--evidence`, `--tool`, `--executable` and `--out`.
Use a trusted absolute executable path without symlinks, outside the case.
The input is a registered piece; output is a new JSON file under `analysis/`.
On Windows, use `py -3` and the approved executable's absolute Windows path.

| `--tool` | Inputs | Optional arguments | Result |
| --- | --- | --- | --- |
| `exiftool` | PNG, JPEG, PDF | None | Grouped numeric metadata JSON |
| `pdftotext` | PDF | `--first-page N --last-page M` | Layout-preserving text with page separators; defaults to page 1, at most 20 pages |
| `tesseract` | PNG, JPEG | `--language eng` or `fra+eng` | OCR text; up to 3 installed three-letter language codes |
| `ffprobe` | WAV, AVI, MP4-family `ftyp`, Matroska/WebM | None | Container/stream JSON; pipe input only, no video frame extraction |

The adapter probes the executable's version (5 seconds), then analyzes a
temporary copy (30 seconds, 512 KiB stdout, 16 KiB stderr). It disables default
ExifTool config loading and restricts ffprobe to a recognized demuxer and the
`pipe` protocol. Some media need seeking unavailable through this input mode.
Executable failures, timeouts, oversized output and malformed JSON fail without
saving a successful analysis. The case is verified before and after execution.
The source is never passed as the working file. Diagnostics can contain private
data; successful stderr is stored only in the local analysis.

These controls do not sandbox third-party binaries or cap their memory and
general filesystem access. Use an appropriate isolated host for hostile files.
The package neither installs binaries/language data nor enables network research.
Missing capabilities remain explicit. See [tool workflows](../shared/tool-workflows.md)
for provenance, output interpretation and separately authorized host web tools.

## Create and populate a case

| Command | Required arguments | Options and behavior |
| --- | --- | --- |
| `init` | `--case`, `--title`, `--scope` | New case only; title ≤ 300 characters, scope ≤ 8,000 |
| `add` | `--case`, `--source` | Optional `--url`, `--origin-group`; copies evidence from outside the case |
| `add-many` | `--case`, repeatable `--source` | Explicit batch; optional shared `--url`, `--origin-group`; 1-5,000 selections within case limits |
| `claim` | `--case`, `--text`, `--state`, `--rationale` | Repeatable `--support` and `--contradict`; default `--confidence low` |

`init` creates `raw/`, `analysis/`, `reports/`, `exports/`, `case.json`,
`evidence.jsonl` and `claims.jsonl`. Scope should describe the objective,
authorized sources and restrictions; it is a recorded statement, not a host
permission engine.

`add` returns the ID, SHA-256 and size. The provenance URL must be HTTPS without
credentials, query parameters or a fragment; the helper **never visits it**.
An origin label is an analyst annotation, not evidence of independence.
A known adjacent `-wal` blocks SQLite intake; supply a coherent backup
produced by the operator.

For many files use `add-many --case CASE --source FIRST --source SECOND`.
It holds one case lock, verifies all registered bytes before intake and verifies
the resulting case before success. It reads one source at a time and returns
the added IDs, hashes and sizes. It does not scan directories. URL and origin
options apply to the entire batch; split batches when provenance differs.
Each addition commits separately: a later failure preserves completed additions.
Run `verify` and inspect the journal before resuming only the remaining files.
Both commands retain source, WAL, path, size and record-limit protections.

`claim` accepts the following states:

| State | Intended meaning | Helper constraints |
| --- | --- | --- |
| `observed` | Observation of evidence content | At least one supporting reference |
| `inferred` | Explicitly justified inference | At least one supporting reference |
| `unconfirmed` | Unestablished proposition | Must have `low` confidence |

A claim accepts at most 100 references per list, with no duplicates or evidence
both supporting and contradicting it. An unresolved contradiction blocks
`high`. Text is limited to 4,000 characters and rationale to 8,000.
The helper checks structure, not citation relevance. Schema 2 adds precise
citations and append-only corrections with --supersedes; old claims remain
historical. Schema 1 retains its original behavior until an explicit upgrade.

## Verify and analyze

| Command | Syntax after the Python prefix | Output and limit |
| --- | --- | --- |
| `verify` | `verify --case CASE` | Inventory, bytes and references; no authenticity proof |
| `provenance` | `provenance --case CASE` | Transitive candidate groups; independence between groups unknown |
| `triage` | `triage --case CASE --evidence E000001 --out CASE/analysis/triage.json` | Signature family, PNG dimensions, ZIP directory or email headers, depending on format |
| `timeline` | `timeline --case CASE --evidence E000001 --out CASE/analysis/timeline.json` | Default `--format json`; also `jsonl` or `csv`; optional `--csv` for a second output |
| `browser` | `browser --case CASE --evidence E000001 --out CASE/analysis/browser.json` | Chromium/Firefox visits, read-only SQLite copy, unverified completeness |
| `correlate` | `correlate --case CASE --input CASE/analysis/a.json --input CASE/analysis/b.json --out CASE/analysis/links.json` | 2 to 20 distinct inputs; exact UTC or URLs; candidate links |

Every analysis `--out` must be a **new file under the case's `analysis/`**.
Its parent must exist; these commands do not create subdirectories. Flat
outputs simplify private exports, which include only files directly
under `analysis/` and `reports/`.

`triage` executes no file and extracts no archive. For PDF and JPEG it reports
family and limits; it provides neither PDF text nor EXIF. Email headers can
be forged. Recognized signature bytes do not validate an entire file.

`timeline` preserves original times. ISO times without offsets are not
converted to UTC. Events without normalized times follow events with UTC,
in source row order. Derived CSV neutralizes cell prefixes that spreadsheets
could interpret as formulas. Its `record_index` preserves the zero-based source
row index, including `0`, even after chronological sorting. Missing timestamp
and UTC values remain empty CSV cells. Older CSV exports may have an empty index
for source row `0`; regenerate them into a new derived file from the original
evidence, keeping the previous export for comparison.

`browser` limits queries to recognized schemas and sets `truncated` beyond
5,000 visits. It collects no live profile, cookies or passwords. A recorded
URL proves neither identity nor intent.
SQLite values/rows are capped at 32 KiB before loading; URLs are preserved
exactly up to 16 KiB and titles accepted up to 8 KiB of UTF-8. Display titles
are limited to 1,000 characters with an explicit `title_truncated` flag.
Fields exceeding these bounds or cumulative output exceeding 4 MiB produce
an error without saving a partial analysis. URLs remain untrusted text;
render them with escaping and do not execute or automatically open them.

`correlate` expects event outputs from `timeline` or `browser`, including their
`input` block. It checks that the ID and hash match the journal. These metadata
remain editable: reproduce analyses before relying on results. Equal times
or URLs do not prove causation.
URLs require `url_exact: true`; legacy analyses without the marker are skipped
and counted in `skipped_unverified_url_count`. Regenerate browser outputs before
correlating. UTC values are normalized before equality comparison.

## Reports and sharing views

```text
report --case CASE [--lang en|fr] [--replace]
prepare-share --input FILE --out NEW_FILE
```

`report` defaults to `en` and writes `reports/report.en.md` or
`reports/report.fr.md`. Headings and labels are localized; claim text is not
automatically translated. `--replace` replaces only that generated path.
The report contains filenames, hashes and `raw/` links and is private by default.
Accepted scope and rationale fields are rendered in full, up to 8,000 characters
each, with markup escaped. Known credential masking recognizes the renderer's
escaped `api_key` spelling as well as plain text; manual review still applies.

`prepare-share` reads UTF-8 text, masks some credentials, email addresses and
IPv4 addresses, removes private report links and recognized SHA-256 values,
then writes a new view. A private-key block is rejected. Destinations under
a component named `raw` are rejected. `review_required` requires human review;
names, locations, identifiers, IPv6 addresses or sensitive inferences may remain.

## Export, verification and restoration

```text
export --case CASE --mode private --out NEW_ARCHIVE
export --case CASE --mode public --view REVIEWED_FILE --approved-sha256 DIGEST --out NEW_ARCHIVE
verify-export --archive ARCHIVE
restore --archive PRIVATE_ARCHIVE --case NEW_CASE
```

A **private** export includes journals, `raw/`, flat derived files and sharing
metadata. It excludes `exports/` itself. Its ZIP is unencrypted: apply suitable
storage and transfer controls. `--view` and `--approved-sha256` are forbidden
in this mode.

A **public** export contains only the approved view, `sharing.json` and the
manifest. After review, compute a digest of the exact bytes:

```bash
sha256sum '/path/to/reviewed-view.md'
```

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\path\reviewed-view.md'
```

Copy the 64 **lowercase** hexadecimal characters into `--approved-sha256`.
Any file change requires a new review and digest. The digest is an operator
statement; it does not certify an approver's identity. Export blocks some
sensitive patterns, control characters and recognized private links, but does
not establish complete anonymization.

`verify-export` checks members without filesystem extraction. `restore`
accepts only a verified private export and a new case with an existing parent.
A verified restoration is moved to its destination; no existing case is merged
or overwritten. Reports and evidence remain confidential after restoration.

## Capabilities and limits

`doctor` describes version, Python, formats and limits without collection.
It does not test AI client permissions or a remote model.

| Runtime limit | Value |
| --- | --- |
| Raw file | 64 MiB, or 67,108,864 bytes |
| Total raw case evidence | 256 MiB, or 268,435,456 bytes |
| Structured JSON/JSONL and analysis output | 4 MiB, or 4,194,304 bytes |
| Journal rows or analyzed events | 5,000 |
| Browser SQLite value/row | 32 KiB |
| Browser URL / accepted title, UTF-8 | 16 KiB / 8 KiB |
| Browser displayed title | 1,000 characters, with `title_truncated` |
| Archive entries examined by `triage` | 1,000 |
| Export members, including manifest | At most 1,024 |

A private export must also fit the 256 MiB limit for members excluding its
manifest, **including evidence and derived files**. A case near the raw limit
can therefore fail to export. ZIP64, multi-disk ZIP and compressed imported
exports are unsupported. Errors are explicit; limits never increase automatically.

## Review, routing and interoperability

[Review workflows and JSON examples](../shared/review-workflows.md) describe
the fields, indexing, limits and interpretation of these offline commands.

| Command | Required arguments | Result |
| --- | --- | --- |
| `plan` | `--kind one supported input kind` | Suggested skills and stop conditions; executes nothing |
| `intake` | `--case`, `--manifest` | Explicit files with individual provenance; committed prefix retained on failure |
| `record` | `--case`, `--input` | Append validated research/entity/relation/annotation JSON |
| `upgrade` | `--case`, `--out` | Verified schema 4 copy of a schema 1, 2 or 3 case |
| `capture` | `--case`, `--evidence`, `--format html or mhtml`, `--out` | Inert capture text, up to 4 MiB input and 100 MIME parts |
| `compare` | `--case`, `--left`, `--right`, `--out` | UTF-8 changes, at most 200,000 bytes and 1,000 lines per input |
| `import-events` | `--case`, `--evidence`, `--time-field`, `--event-field`, `--out` | Selected CSV fields, original indices and unmapped-column list |
| `export-events` | `--case`, `--input analysis/events.json`, `--out` | Timesketch-field CSV, normalized times only; reports omissions |
| `graph` | `--case`, `--out`; optional `--format json or graphml` | Evidence-linked relations and candidate status |

`claim` accepts `--citations FILE` (JSON array) and `--supersedes C_ID` in schema 2 or 3.
`report --format html` writes the fixed private report path; repeat
`--input analysis/events.json` for up to 20 selected event analyses (5,000 events
total). `--lang en` is default; FR translates interface labels, not evidence.
The diagram displays at most 150 nodes and 500 edges; larger graphs remain
available in the complete graph export and relation list. All HTML is bounded
to 4 MiB. No network resource or external library is loaded.

`tool-run --reuse analysis/previous.json` explicitly reuses a compatible previous
analysis after identity checks and a version probe. Omit it for fresh execution.
No automatic cache, model call or tool installation is performed.

## Contextual planning and review

Research helpers offer `pivots [--kind KIND]` and
`queries --kind domain|organization|publication --value TEXT [--site DOMAIN]`.
These return suggestions without collecting or searching; see
[follow-up checks](../shared/research-workflows.md).
`dorks --phrase TEXT [--site DOMAIN] [--filetype TYPE] [--exclude TEXT]`
`[--after YYYY-MM-DD] [--before YYYY-MM-DD]` composes a Google query and URL.
Repeat `--exclude` up to five times. The model may execute the query through
authorized host web tools; the Python command stays offline.
[Operators, input bounds and execution workflow](../shared/research-workflows.md#google-dorking-with-host-web-tools).
`mcp [--case CASE]` starts the optional read-only stdio interface; see
[MCP setup](mcp.md) before configuring a host.

```text
plan --kind organization
plan --request selected-plan.json [--case CASE]
sources [--category organization|domain|archive|imagery] [--jurisdiction FR]
claim ... [--depends-on C000001] [--time-context dates.json]
review-status --case CASE
review-queue --case CASE [--limit 20]
check-citations --case CASE
agent-events --case CASE --evidence E000001 --format json|jsonl --out CASE/analysis/agent.json
```

The [review controls](../shared/assurance-workflows.md) define request fields,
capability declarations, warning propagation, citation results and coverage
requirements. Plans are advisory and do not launch tools. Excerpt checks compare
qualified original lines/records or bound derived output; they never establish
semantic support. Mismatches remain reportable review findings, while broken
hash/reference integrity still fails verification.

`review-queue` returns current review tasks with priority, references, a suggested
skill and next check. `--limit` accepts 1-100 (default 20); totals include omitted
items. Priorities order work and are not confidence scores. Unavailable sources
may warrant an explicit limitation. An empty queue does not establish completeness
or truth. The command checks integrity, leaves files unchanged and executes no
suggestion. Historical claims remain verified but are excluded from this queue.
If a case journal changes during assembly, it fails with
`CASE_CHANGED_DURING_REVIEW`; rerun after the writer finishes.

The [source profiles](../shared/source-workflows.md) are dated documentation,
not API integrations. The [agent export schema](../skills/of-agent-artifacts/references/workflow.md)
requires selected normalized data. No command discovers profiles, executes
recorded tool calls, installs software or performs network research.

New cases use schema 4; schemas 1, 2 and 3 remain readable. Use
`upgrade --case OLD --out NEW` to create a verified copy before recording new
semantics. Existing journals and original cases are preserved.

## Schema 4 investigation workflow

`record` also accepts validated `hypothesis`, `test` and citation-level `origin`
records. See the [JSON recipes](../shared/recipes.md) and the
[record contract](../shared/case-contract.md#schema-4-investigation-records).
The review queue includes unfinished tests and tests whose hypothesis changed.
HTML and Markdown reports retain their evidence, predictions and outcomes.
Same-kind `supersedes` can revise entities, relations and requirements. A complete
replacement with `retired: true` withdraws an assertion without rewriting it.

`plan --max-steps 8` budgets actual actions. Optional `--resume-from`, repeated
`--completed-step KIND:PHASE`, repeated `--available-input` and `--stop-reason`
control a declared continuation. A selected `--case` prioritizes its recorded
review tasks before generic material checks. `--specialize` returns advisory
read-only host tasks and one case writer. It launches no agents or collection.
The JSON request also supports bounded `available`, `authorized` and
`deferred_leads`. Missing input/capability/prerequisite states remain visible.

`sources --applicable-to FR` includes bundled global and applicable regional
cards. `--jurisdiction FR` retains its exact-match behavior. These modes cannot
be combined. Cards remain dated documentation, not tested API availability.

## Native selected agent exports

```bash
python3 scripts/forge.py agent-events --case CASE --evidence E000001 --format codex-exec-jsonl --exporter-version VERSION --out CASE/analysis/agent-events.json
```

Only the documented Codex `exec --json` event export is interpreted by this
adapter. It never discovers session files or live profiles. The original stays
registered. Derived events retain physical-line indices, item IDs, declared
exporter version, omitted/unknown fields and reported statuses. Requests without
results and duplicate or ambiguous calls remain gaps. A reported completion
does not prove execution or an external effect.

## Public exports and timed transcripts

Register each selected original using `add`, then run one of these offline commands.
Outputs must be new files under `CASE/analysis`.

| Command | Required selection | Optional context |
| --- | --- | --- |
| `wayback-index --case CASE --evidence E_ID --url URL --out FILE` | Exact original URL from a CDX JSON table | `--after` and `--before`, inclusive ISO capture dates |
| `bodacc-history --case CASE --evidence E_ID --siren SIREN --out FILE` | Nine-digit identifier from a BODACC JSON export | `--event-date-field FIELD`, an explicit top-level ISO date distinct from publication |
| `transcript --case CASE --evidence E_ID --format srt\|vtt --out FILE` | Supplied UTF-8 subtitle file | `--method unknown\|manual\|automatic`, `--translation unknown\|original\|translated`, `--language TEXT` |

Use [command recipes](../shared/recipes.md#read-a-supplied-archive-index-company-export-or-transcript)
and [accepted formats](../shared/source-workflows.md#supplied-public-exports-and-timed-transcripts).
Each analysis carries original provenance, source indexes and interpretation
limits. BODACC publication dates have no invented time or timezone. Transcript
offsets are media-relative and are omitted from wall-clock Timesketch exports.
The commands do not retrieve archives, call registries or transcribe media.

To replay an original synthetic case from sources or the full plugin archive:

```bash
python3 examples/public_imports_demo.py --out /tmp/forge-public-imports-demo
```

Use a new destination. The demo checks citations and creates local HTML reports
and a private export with restoration. It does not call a model or the network.

## Qualified derived text and PDF pages

`compare` accepts one original E selector or one qualified analysis selector
per side. Derived selectors require their exact hashes:

```bash
python3 scripts/forge.py compare --case CASE --left-analysis analysis/first.json --left-sha256 HASH --right-analysis analysis/second.json --right-sha256 HASH --out CASE/analysis/comparison.json
```

The output retains both original E IDs and hashes, extraction identities and
coverage. A second extraction of one original is not independent evidence.
Page citations can reference bounded `pdftotext` analyses with exact hashes and
unambiguous page separators/coverage. Empty pages and starting offsets are kept.
Unsupported or uncertain mappings remain unverifiable. Millisecond citations
still need separately qualified timing evidence and analyst review.

## Concurrent reads and bounded work

Reports, citation checks, graphs, plans and review share verified read state.
Per-operation caches expire afterward. Concurrent changes fail with
`CASE_CHANGED_DURING_READ` or `CASE_CHANGED_DURING_REVIEW` before the result is
accepted. Private export publication occurs after this coherence check.
Source changes, byte limits and cancellation never become successful excerpts.
The optional MCP adds bounded work and cancellation without blocking pings.
Each platform also performs a final streaming byte check, because rapid same-size
rewrites can retain identical filesystem timestamps. It adds one integrity read
per selected file without repeating the parse for each citation.
