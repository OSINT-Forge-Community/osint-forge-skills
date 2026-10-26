# Data formats and semantics

The [contract v3](../shared/case-contract.md) defines the invariants.
This guide provides fields and examples for reviewing or preparing inputs.
Journal examples illustrate the format; create records with `init`, `add`
and `claim`, never by inventing hashes.

## Private case layout

```text
case/
├── case.json
├── evidence.jsonl
├── claims.jsonl
├── review.jsonl
├── raw/E000001.bin
├── analysis/timeline.json
├── reports/report.en.md
└── exports/private.zip
```

Structured data is UTF-8 JSON. JSONL uses one JSON object per nonempty line.
IDs are local to the case: `E` or `C` followed by six digits. Recorded paths
use `/` on every platform. The `.bin` extension preserves original bytes
without content conversion.

## `case.json`

| Created field | Value or meaning |
| --- | --- |
| `schema_version` | Integer `3` for new cases; `1` and `2` remain readable, separate from product version |
| `tool_version` | Tool version at creation |
| `title` | Investigation title, 1 to 300 characters |
| `scope` | Objective and limits, 1 to 8,000 characters |
| `created_at` | Local acquisition time recorded in UTC |
| `acquisition_authenticity` | `not_established` |
| `model_trials` | Empty at creation; no model proof generated automatically |

The loader checks schema version, title and scope, among other fields.
It does not authenticate all free-form metadata. A local timestamp is not
external attestation and may depend on the workstation clock.

## `evidence.jsonl`

Every appended row contains:

| Field | Meaning |
| --- | --- |
| `id` | For example `E000001`, unique within the case |
| `path` | Exactly `raw/<id>.bin` |
| `sha256` | 64 lowercase hexadecimal characters for the copied file |
| `size` | Byte size, a nonnegative integer |
| `original_name` | Source basename, not its full path |
| `collected_at` | Recorded copy time, separate from event time |
| `source_url` | HTTPS URL meeting CLI restrictions, or `null` |
| `origin_group` | Analyst label, or `null` |
| `origin_independence` | `unverified` at intake |

Equal hashes group identical bytes. Equal `origin_group` labels group evidence
assigned by the analyst to a shared origin. Grouping is transitive. Separate
groups do not automatically become independent. Labels need a basis in observed
attribution, chronology and editorial ownership.

## `claims.jsonl`

Schematic example, valid once the cited evidence has been registered:

```json
{
  "id": "C000001",
  "text": "Both captures mention the same attribution.",
  "supports": ["E000001", "E000002"],
  "contradicts": [],
  "state": "observed",
  "confidence": "medium",
  "rationale": "Observation of the text; the event itself remains unestablished."
}
```

In the real file, this object occupies one line. `supports` and `contradicts`
contain existing IDs without duplicates or overlap. `state` is `observed`,
`inferred` or `unconfirmed`; `confidence` is `low`, `medium` or `high`.
Constraints are in the [CLI reference](cli.md). These states are qualitative;
the runtime computes no probability score.

## Timeline input

Chronologies sort by instant, including fractions of a second. Equal instants
keep source order. Offset conversion beyond years 1-9999 produces an `invalid`
time while retaining the event and original timestamp.

`timeline` accepts three representations:

- JSON: an object array or an object whose `events` field is an array.
- JSONL: one object per nonempty line.
- CSV: `timestamp,event` headers, then one row per event.

JSON example:

```json
[
  {"timestamp": "2026-10-01T09:00:00+02:00", "event": "Announcement published"},
  {"timestamp": "2026-10-01T09:00:00", "event": "Stated time without a timezone"},
  {"timestamp": null, "event": "State observed without a recorded time"}
]
```

`event` must be a string of 1 to 4,000 characters. `timestamp` may be a string,
`null` or absent. An unparseable string becomes `invalid`; incompatible types
are rejected. Extra fields are not retained by the timeline: keep the raw
evidence to recover them.

| Derived `time_status` | `utc` | Interpretation |
| --- | --- | --- |
| `normalized` | UTC time | Explicit offset converted, or recognized browser epoch |
| `timezone_unknown` | `null` | Parseable date without an explicit offset |
| `missing` | `null` | Absent or empty value |
| `invalid` | `null` | Unparseable value |

Each derived event retains `evidence_id`, zero-based `record_index`, `event`,
`original_timestamp`, `utc` and `time_status`. Displayed text may neutralize
invisible control characters; raw evidence remains intact.

## Analysis outputs and correlation

CLI analyses have an input block:

```json
{
  "input": {
    "evidence_id": "E000001",
    "sha256": "actual evidence digest, 64 hexadecimal characters"
  }
}
```

This illustration is not a usable digest. The CLI supplies the real value.
A timeline adds `events`, `event_count`, `uncertain_time_count` and `limitations`.
Browser analysis also adds `family`, `granularity`, `snapshot_completeness` and
`truncated`; its events contain `url`, `url_exact`, `title`, `title_truncated`
and `timestamp_encoding`. `url` is exact untrusted text, bounded to 16 KiB of
UTF-8, with `url_exact: true`. Title display is clipped at 1,000 characters;
`title_truncated` records that loss. Source titles may contain up to 8 KiB.
SQLite values/rows exceeding 32 KiB and cumulative oversized analyses are rejected.

Chromium encodes visits in microseconds since January 1, 1601 UTC; Firefox
uses microseconds since January 1, 1970 UTC. Queries cover only supported tables.
Conversion establishes neither clock accuracy nor history completeness.

`correlate` receives referenced event analyses and returns `candidate_links`:
`basis` (`same_utc` or `same_url`), a common value and references to input rows.
The result is an investigative lead, with no proof of identity, causation or
independent sources.
`skipped_unverified_url_count` counts legacy URL fields without `url_exact: true`.
Regenerate those browser analyses; old clipped values cannot establish equality.
UTC equality uses normalized instants, including equivalent fractional notation.

## External-tool analyses

`tool-run` adds `analysis_type: external_tool` and the same original `input`
reference. `tool` records the selected name, absolute executable path, reported
`version_output`, argument array and zero return code. `started_at` and
`finished_at` are local UTC observations, not trusted timestamps.

`stdout` retains UTF-8 output and `stdout_sha256` hashes its original bytes.
`result` contains parsed JSON for ExifTool/ffprobe or text for pdftotext/Tesseract.
`stderr` is decoded diagnostic text; invalid UTF-8 is replaced, while
`stderr_sha256` refers to the original diagnostic bytes. `coverage` records
requested PDF pages or single-file mode; it does not certify completeness.
`limits` and `limitations` preserve the execution bounds and interpretation gaps.

Input-copy filesystem timestamps describe a derived working file. OCR, tags,
tool paths and diagnostic output can be sensitive or misleading. Keep them
private, verify relevant fields and cite the original E ID with the analysis
path. A transformed output is not independent corroboration. No case schema
change or migration is needed; these are derived JSON files.

## Case archives

| Archive | Contents | Can it restore a case? |
| --- | --- | --- |
| Private | Journals, evidence, flat derived files, `sharing.json`, manifest | Yes, into a new directory |
| Public | Reviewed view as `report.md`, `sharing.json`, manifest | No |

`export-manifest.json` has `schema_version: 1`, `tool_version`, `integrity_scope`
and `files`. Each member except the manifest is described by `path`, `size` and
`sha256`. Internal hashes check consistency; independently retain the archive
hash if detecting replacement of the entire archive is required.

ZIP members are stored without compression and use a fixed technical date,
**with no acquisition meaning**. No encryption or release signature is added.
Skill distribution archives are separate products: they are not restorable
investigation cases.

## Contract evolution

Readers accept versions 1, 2 and 3. New cases use 3; other versions are rejected.
Older cases retain their original operations. `upgrade --case OLD --out NEW`
copies a verified private case and records the old export digest. A v1 copy gains
a review journal; a v2 copy keeps its journal unchanged. OLD is preserved. Older
readers reject v3.
Never edit the schema number to bypass compatibility checks.

## Review extension (schema 2)

Claims optionally contain `citations` and `supersedes`, and new v2 claims record
`recorded_at`. Citations include evidence_id, kind, inclusive start/end, optional
quote and, for derived analyses, analysis plus sha256. Page/line numbering starts
at 1; record/time_ms at 0. Excerpts are capped at 2,000 characters, 100 locators
per claim. `supersedes` points to an earlier current C ID; cycles and forks are
rejected. An old claim is retained as historical.

`review.jsonl` contains R IDs and kinds research, entity, relation and annotation.
Each record has recorded_at and rationale; evidence references are checked.
Research requires question, query, scope, tool and a coverage status. Entities
require a type, label and evidence; relations require two existing entities,
a label, evidence and observed/candidate state. An annotation requires analysis,
sha256, zero-based record_index, tags, note and rationale. Its analysis digest
and original input are checked. Research/annotation revisions use supersedes.

See [review workflows](../shared/review-workflows.md) for complete examples.
No record is an authenticated signature, automatic identity resolution or proof
that a conclusion follows from its citations.

## New derived formats

`wayback_cdx`, `bodacc_history` and `timed_transcript` analyses use the existing
`input` provenance object and `events` array. No case schema migration is needed.
Each event retains its source `record_index` even when publication/capture rows
are sorted. CDX indexes exclude the header from record numbering. BODACC indexes
refer to the original object array or `results` array, before SIREN selection.
Transcripts number cues from zero, excluding metadata blocks, and also store
one-based inclusive source line ranges.

CDX events retain original columns in `cdx`, plus a declared UTC capture time.
BODACC events retain the complete supplied row in `notice`, `notice_id`,
`publication_date` and a separately selected `event_date` or null. Their `utc`
is null. Transcript events retain the verbatim cue payload in `event`, start/end
milliseconds, original time strings, cue ID and uninterpreted settings. They
have no wall-clock timestamp. Method, language and translation are declarations.

A `time_ms` citation on a `timed_transcript` analysis can be checked against
stored cue text. Its start/end must exactly enclose all intersecting cues.
Cue intervals are treated as start-inclusive and end-exclusive for overlap
selection. Partial cue boundaries are rejected because word timing is unknown.
Bind the analysis path and hash, as with record citations. This check cannot
verify audio, translations, speakers or the semantic support for a claim.

See [accepted input shapes and bounds](../shared/source-workflows.md#supplied-public-exports-and-timed-transcripts).

Mapped CSV analyses retain original record_index, normalized or uncertain time,
selected event text and unmapped column names. HTML/MHTML capture analyses retain
text and untrusted declared locations, never execute scripts or fetch resources.
Text comparisons reference both original inputs and one-based changed ranges.
Graph JSON/GraphML retains local evidence/claim/entity IDs and relation status.
Timesketch CSV omits uncertain times and reports the count; other fields and
annotations remain in the original analysis. All such outputs remain private.

Tool analyses record reuse_identity (input digest, executable digest, version
and arguments), execution and, when reused, reused_from and reused_at. Reuse
checks stored stdout and parsed output consistency. It is not fresh execution
or independent verification; runtime libraries and OCR language data are not
part of the identity. Reproduce untrusted results instead.

## Schema 3 review extensions

The [planning and evidence review guide](../shared/assurance-workflows.md)
defines earlier-claim dependencies, time context, requirements, analysis revisions
and entity identifiers. New features require schema 3; migrate old cases by
verified copy. Review warnings and excerpt checks are derived assessments, not
rewrites of the journals or semantic truth validation.

The [agent export contract](../skills/of-agent-artifacts/references/workflow.md)
defines the explicit normalized JSON/JSONL input for `agent-events`. Native
client logs are not guessed or acquired. Unknown event types remain gaps.

## Schema 4 investigation and revisions

New cases use schema 4. Schemas 1, 2 and 3 remain readable. Upgrade by verified
copy before adding new semantics. The
[schema 4 record contract](../shared/case-contract.md#schema-4-investigation-records)
defines hypotheses, discriminating tests, assertion origins and same-kind
revisions/withdrawals for entities, relations and requirements. Current views
exclude superseded/withdrawn records, while journals preserve their full history.

Tests bind an earlier hypothesis R identifier to an expected observation and
declared outcome. A revised hypothesis makes its earlier tests review work.
Origins bind a claim and zero-based citation index to a documented upstream
group. Shared groups indicate declared common provenance, not independent
corroboration. Direct observations also require a basis and evidence.

`codex-exec-jsonl` is a separate explicit input profile for selected public
Codex CLI event exports. Original physical indices, item IDs, reported statuses,
exporter context, unmapped field counts and omission gaps remain in the derived
analysis. No private internal rollout format or live profile is collected.
