# Investigation command recipes

Run from the complete loaded skill folder. Examples use `python3`, an existing
`/tmp` parent and new case names. On Windows use `py -3` and an existing local
parent. Replace paths and use the E/R/C identifiers actually returned by commands.
The snippets below assume a new case populated in the shown order.

## Read a supplied archive index, company export or transcript

After registering each original with `add`, use the returned evidence ID.
These examples use three separately registered pieces in one existing case.
No command acquires public data or verifies audio.

```bash
python3 scripts/forge.py wayback-index --case /tmp/forge-recipe-01 --evidence E000001 --url https://example.org/notice --after 2026-01-01 --before 2026-12-31 --out /tmp/forge-recipe-01/analysis/captures.json
python3 scripts/forge.py bodacc-history --case /tmp/forge-recipe-01 --evidence E000002 --siren 000000000 --out /tmp/forge-recipe-01/analysis/notices.json
python3 scripts/forge.py transcript --case /tmp/forge-recipe-01 --evidence E000003 --format vtt --method automatic --translation unknown --language fr --out /tmp/forge-recipe-01/analysis/transcript.json
```

The all-zero SIREN is a synthetic fixture selector, not a real company example.
Read [accepted formats and limits](source-workflows.md#supplied-public-exports-and-timed-transcripts).
Reference a derived `record` using its preserved `record_index`, analysis path
and SHA-256. For transcripts, a `time_ms` citation must cover complete intersecting
cues with exact outer start/end boundaries. The excerpt check validates stored
cue text, never spoken words or their exact timing.

## Start with one selected piece

```bash
python3 scripts/forge.py doctor
python3 scripts/forge.py init --case /tmp/forge-recipe-01 --title 'Synthetic review' --scope 'Selected synthetic records only'
python3 scripts/forge.py add --case /tmp/forge-recipe-01 --source /path/to/selected-copy.txt
python3 scripts/forge.py triage --case /tmp/forge-recipe-01 --evidence E000001 --out /tmp/forge-recipe-01/analysis/triage.json
python3 scripts/forge.py verify --case /tmp/forge-recipe-01
```

The selected copy must already exist outside the case. `add` does not acquire
evidence or establish its authenticity. For several explicitly selected pieces,
use `add-many --source FIRST --source SECOND`. Verify partial batches before retry.

## Record a precise citation

Prepare the exact selected range instead of typing a partial quotation:

```bash
python3 scripts/forge.py prepare-citation --case /tmp/forge-recipe-01 --evidence E000001 --kind line --start 1 --end 1 --out /tmp/forge-recipe-01/analysis/citations.json
python3 scripts/forge.py claim --case /tmp/forge-recipe-01 --text 'The selected passage contains the quoted statement.' --state observed --support E000001 --confidence medium --rationale 'Observation of the supplied passage, without independent factual verification.' --citations /tmp/forge-recipe-01/analysis/citations.json
python3 scripts/forge.py check-citations --case /tmp/forge-recipe-01
```

Read the prepared excerpt before recording the claim. The output file is a
claim-ready JSON array, not an evidence analysis. The command computes the
original hash and any selected analysis hash. It does not record a claim or
validate meaning. Quotes must cover the whole selected range, up to 2,000
characters. Narrow the range or select a record field if it is too long.
For a single long line, retain a locator without a quote and disclose that
no exact quotation was compared instead of silently truncating the source.

For an imported BODACC notice use `--kind record --analysis analysis/bodacc.json
--start 0 --end 0 --field notice`. This includes the notice fields instead of
only the generic event label. For Wayback use `--field cdx` on its qualified
analysis. Original `record_index` values remain valid after sorting.
Raw JSON record citations need `--format json` and index the actual array,
including its header row when present. JSON envelopes need a qualified import
or text-line citation. Prepared excerpts never prove authenticity.

A PDF page citation selects a qualified `pdftotext` analysis and its actual
SHA-256. Original PDF page numbers follow the adapter's selected first/last
page range. Empty pages and page boundaries remain significant.

```json
[{"evidence_id":"E000001","kind":"page","start":2,"end":2,"analysis":"analysis/pdf-text.json","sha256":"REPLACE_WITH_ACTUAL_ANALYSIS_SHA256","quote":"Exact extracted passage"}]
```

## Hypotheses and tests

New schema 4 cases support structured alternatives and tests. Upgrade an older
case by verified copy before using these records. Save each JSON object to a
selected file, then append it with `record --case CASE --input FILE`.

```json
{"kind":"hypothesis","label":"Implementation occurred","statement":"The supplied announcement describes an implemented event.","status":"candidate","prediction":"A separate implementation record should describe the event.","alternatives":[],"evidence":["E000001"],"rationale":"The announcement alone does not establish implementation."}
```

Use the returned R identifier in a test:

```json
{"kind":"test","hypothesis":"R000001","action":"Compare the selected implementation record with the announcement.","expected":"The implementation record identifies the same event and date.","status":"blocked","outcome":"undetermined","evidence":[],"rationale":"The required implementation record has not been supplied."}
```

For a completed test, retain its observation and supporting E references.
Append a revised record with `supersedes` when its state changes. A test result
describes the recorded check, without automatically proving its hypothesis.
Use `retired: true` only with a complete superseding record and a reason for
withdrawal. Never delete a rejected hypothesis or rewrite its earlier evidence.

## Assertion origins

An article can copy one assertion and independently observe another. Use the
actual claim and zero-based citation index, with evidence explaining attribution:

```json
{"kind":"origin","claim_id":"C000001","citation_index":0,"origin_group":"synthetic-bulletin","relationship":"copied","basis":"The selected passage explicitly attributes this statement to the bulletin.","evidence":["E000001"],"rationale":"Attribution applies to this assertion, not every passage in the publication."}
```

Origin groups organize source relationships. Different groups do not establish
independence, and `direct_observation` is an analyst assertion requiring evidence.

## Selected agent exports

Register a supplied Codex `exec --json` capture with `add`, then select its
format explicitly. This command reads the registered copy without locating
profiles or making calls recorded in the capture:

```bash
python3 scripts/forge.py agent-events --case /tmp/forge-recipe-01 --evidence E000001 --format codex-exec-jsonl --exporter-version supplied-version --out /tmp/forge-recipe-01/analysis/agent-events.json
```

For `of-agent-events-v1` use `--format json` or `--format jsonl`. Review orphan
requests, duplicate IDs, omitted metadata and clipping gaps. Reported results
and version labels remain unverified assertions. Cite the original record index.

## Resume and deliver privately

```bash
python3 scripts/forge.py review-queue --case /tmp/forge-recipe-01 --limit 20
python3 scripts/forge.py report --case /tmp/forge-recipe-01 --lang en --format html
python3 scripts/forge.py verify --case /tmp/forge-recipe-01
python3 scripts/forge.py export --case /tmp/forge-recipe-01 --mode private --out /tmp/forge-recipe-01/exports/handoff.zip
python3 scripts/forge.py verify-export --archive /tmp/forge-recipe-01/exports/handoff.zip
```

The private archive contains original evidence. For exact-view public sharing,
read the [sharing contract](case-contract.md#sharing-and-portability). An empty
review queue is not a truth, completeness or publication-readiness verdict.
