# Troubleshooting and error recovery

For `CASE_CHANGED_DURING_READ` or `CASE_CHANGED_DURING_REVIEW`, wait for the
authorized writer to finish, run `verify`, then repeat the read operation.
Do not disable integrity checks or reuse the rejected result. An export refused
during capture has not published its output archive.

`INVALID_CSV_HEADERS`, `INVALID_CSV_ROW` or `INVALID_EVENT_MAPPING` can indicate
duplicate/empty column names or inconsistent row widths. Preserve the original
and request a corrected export. Do not silently choose one duplicate column.

`CITATION_PAGE_MAPPING_UNCERTAIN` means extracted page separators do not match
the declared range. Review the pages or provide a newly qualified extraction.
`CASE_UPGRADE_REQUIRED` for investigation records requires `upgrade --case OLD
--out NEW`; never edit schema metadata in place.

Installer `INSTALL_UPDATE_REQUIRED` requires an explicit targeted `update`.
`INSTALL_BUSY` means another operation owns the client/scope lock.
`INSTALL_TRANSACTION_PENDING` or `INSTALL_RECOVERY_REQUIRED` requires a recovery
preview. `INSTALL_RECOVERY_CONFLICT` and `INSTALL_TRANSACTION_CONTENT_CHANGED`
preserve conflicting bytes for operator review. `INSTALLATION_TOO_LARGE` rejects
an operation beyond the bounded payload. See [installation recovery](installation.md).

MCP `OPERATION_BUDGET_EXCEEDED` and `OPERATION_CANCELLED` do not establish a
completed verification. `CASE_TOOL_BUSY` allows one expensive case operation at
a time. Reduce the selected case or rerun a bounded operation after completion.

Start by recording the **command, fixed code and step**, without copying private
evidence. Avoid repeating a mutation without knowing its outcome. `verify`
and `verify-export` are the first read-only checks. Never resolve a preservation
error by deleting the journal or original evidence. The helper performs no
automatic recovery.

## Supplied public exports and transcripts

| Code | Meaning and next step |
| --- | --- |
| `DUPLICATE_JSON_KEY` / `INVALID_IMPORT_JSON` | Ambiguous or invalid JSON. Preserve the original and obtain a valid export. |
| `INVALID_CDX_HEADERS` / `INVALID_CDX_ROW` / `INVALID_CDX_TIMESTAMP` | Expected a CDX JSON header table with exact row widths and 14-digit calendar timestamps. Do not substitute a provider error response. |
| `INVALID_IMPORT_URL` / `INVALID_DATE_WINDOW` | Select an HTTP(S) URL without credentials or whitespace and a chronological ISO date window. |
| `INVALID_BODACC_ROWS` / `INVALID_BODACC_REGISTER` / `INVALID_SIREN` | Check the documented flat/v2 JSON shape and nine-digit string identifiers. Names are not fallback selectors. |
| `INVALID_IMPORT_DATE` / `INVALID_EVENT_DATE_FIELD` | Use a valid ISO date and keep the selected act-date field distinct from `dateparution`. |
| `INVALID_WEBVTT_HEADER` / `INVALID_TRANSCRIPT_CUE` / `INVALID_CUE_TIME` / `INVALID_CUE_INTERVAL` | Check the original subtitle format, blank separators and strictly increasing start/end within each cue. Request a separate corrected export. |
| `EMPTY_TRANSCRIPT` / `INVALID_CUE_TEXT` | No supported cues, an oversized payload or an ambiguous cue boundary. Do not treat this as an empty verified transcript. |
| `STRUCTURED_INPUT_TOO_LARGE` / `TOO_MANY_RECORDS` / `ANALYSIS_OUTPUT_TOO_LARGE` | Supply a bounded export with its selection context. No partial analysis was saved. |
| `CITATION_RANGE_MISMATCH` | For transcript intervals, select exact outer boundaries enclosing every intersecting cue. Partial words cannot be timed from cue-level data. |

See [accepted shapes and limits](../shared/source-workflows.md#supplied-public-exports-and-timed-transcripts).

## Installation and builds

| Code or symptom | Cause to check | Action |
| --- | --- | --- |
| Python missing or too old | Interpreter in the current shell | Use Python 3.11+; `py -3` on Windows or `python3` on Linux/WSL |
| `PATH_MISSING` / `DIRECTORY_REQUIRED` | Missing parent, target or source | Check path and current directory; create only the intended parent |
| `PACKAGE_DRIFT` | `dist/` no longer matches sources | Review changes, rebuild with `scripts/package.py`, then run `--check` |
| `SKILL_RESOURCE_DRIFT` | A skill's generated runtime, common guides or license differs from its shared source | Review changes, run `scripts/package.py --sync-skills`, then `--sync-skills --check`; reinstall existing copies explicitly |
| `UNEXPECTED_SKILL_FILE` | An unrecognized file is present inside a skill's generated runtime | Preserve and review the file; synchronization refuses to delete it or partially update other skills |
| `PACKAGED_RUNTIME_REQUIRED` | An installed skill is incomplete or predates the standalone-folder distribution | Reinstall the complete skill folder, including `scripts/forgekit/` and shared references; no runtime is downloaded automatically |
| `UNEXPECTED_BUILD_FILE` | Unexpected file in `dist/` | Inventory and preserve the file before an operator decision; avoid broad cleanup |
| `UNEXPECTED_PACKAGE_INPUT` | Unplanned file in a packaged directory | Exclude personal content from the public scope or investigate the new type |
| `VERSION_MISMATCH` | Sources from different versions | Use a consistent set of files for the selected version; report reproducible defects |
| `SKILL_COLLISION` | A same-name skill already exists | Choose a fresh workspace or preserve and remove the existing installation through its normal route |
| `INSTALL_ALREADY_EXISTS` | Receipt already exists for client/scope | Review the installation and changes; the installer has no in-place update |
| `INSTALLED_FILE_MODIFIED` | An installed copy changed | Preserve the change and compare with the receipt; no automatic partial deletion |
| `INVALID_INSTALL_RECEIPT` | Invalid receipt or incompatible checkout | Preserve state and investigate with the version used to install |
| Skill invisible in a client | Wrong environment, path or version | Check Windows/WSL, scope and directory; restart the session according to client documentation |

The standalone adapter uses a separate receipt for each client/scope pair.
`--skill` applies only to installation; removal follows the whole receipt.
Manage native installations with the host CLI, not manual registry changes.
See [installation](installation.md) for available routes.

## Cases and evidence

| Code | Meaning | Safe action |
| --- | --- | --- |
| `CASE_EXISTS` / `OUTPUT_EXISTS` | Destination already in use | Choose a new name; consider `--replace` only for a generated report |
| `CASE_BUSY` | `.forge.lock` exists | Stop mutations and check whether an operation remains active |
| `RAW_INVENTORY_MISMATCH` | Missing or unindexed raw file | Preserve the entire case and compare journal/inventory; restore a verified backup into a new case |
| `EVIDENCE_INTEGRITY_MISMATCH` | Size or hash differs from the journal | Preserve the discrepancy, check source and backup; do not recalculate the journal to hide it |
| `SOURCE_CHANGED` | Source changed during reading | Supply a stable operator-produced copy, then check it |
| `SOURCE_MUST_BE_OUTSIDE_CASE` | Attempt to reimport from the case | Select the explicitly authorized external original |
| `SQLITE_WAL_PRESENT` | Adjacent SQLite WAL | Request a coherent backup; do not delete the WAL to pass validation |
| `SYMLINK_REJECTED` / `REGULAR_FILE_REQUIRED` | Link or special file | Use an authorized regular copy under a trusted parent |
| `PROHIBITED_PATH` | `envs/production` path | Stop this action; use fixtures or a local non-production export |
| `UNSUPPORTED_CASE_SCHEMA` | Schema other than V1 or invalid type | Use a compatible reader; V1 has no automatic migration |
| `INVALID_SOURCE_URL` | URL violates requirements | Record HTTPS without credentials, query or fragment; never insert a token |

### Resume after interruption

1. Check that no command is still working on the case. Identify the interrupted
   operation from operator context without killing an unknown process or
   opening secrets.
2. Preserve an independent copy of the state and useful hashes. Incomplete
   elements are part of the observation; do not erase them to obtain `verified`.
3. Compare `evidence.jsonl` with the `raw/` inventory, then with originals and a
   verified backup. Validation may stop at the lock first.
4. Decide with the operator whether the lock is residual. Any removal must be
   documented after checking, never an automatic action proposed by the AI.
5. Prefer `restore` from a verified private export into a **new** case. Replay
   necessary additions from preserved sources and record what was resumed.
   IDs belong to each case.

V1 has no `repair` command, guaranteed multi-file transaction or automatic
recovery journal. Without a backup, reconstruction must be documented under
operator control, rather than resetting state.

## Claims and analyses

| Code | Action |
| --- | --- |
| `FACT_WITHOUT_EVIDENCE` | Add relevant evidence or retain an `unconfirmed` proposition with rationale |
| `UNCONFIRMED_CONFIDENCE` | Keep `low` while the proposition is unestablished |
| `UNRESOLVED_CONTRADICTION` | Retain the contradiction and revise confidence; do not remove evidence to pass |
| `INVALID_EVIDENCE_REFERENCE` / `OVERLAPPING_REFERENCES` | Check existing IDs, duplicates and the role of each reference |
| `ANALYSIS_OUTPUT_REQUIRED` / `ANALYSIS_INPUT_REQUIRED` | Use derived files under the selected case's `analysis/` |
| `ANALYSIS_PROVENANCE_MISSING` / `ANALYSIS_PROVENANCE_MISMATCH` | Reproduce analysis with the helper and verified evidence |
| `EVENT_ANALYSIS_REQUIRED` | Correlate event outputs, not a triage result |
| `INVALID_TIMELINE_INPUT` / `INVALID_TIMELINE_ROWS` | Review UTF-8 encoding and JSON, JSONL or CSV structures in [data formats](formats.md) |
| `SQLITE_REQUIRED` / `UNSUPPORTED_BROWSER_SCHEMA` | Supply a supported history snapshot; no fallback parser is installed |
| `SQLITE_ANALYSIS_FAILED` | Examine the copy/backup with an authorized local tool; do not disable bounds |
| `BROWSER_FIELD_TOO_LARGE` | URL exceeds 16 KiB or title exceeds 8 KiB of UTF-8; request a bounded derived export and preserve the original |
| `INVALID_BROWSER_ROW` / `INVALID_BROWSER_REFERENCE` | Snapshot has unexpected field types or missing/ambiguous visit references; verify its schema and acquisition |
| `INVALID_BATCH_SIZE` | Select 1-5,000 explicit sources for `add-many`; respect remaining case and journal capacity |
| `FILE_TOO_LARGE` / `CASE_TOO_LARGE` / `STRUCTURED_INPUT_TOO_LARGE` | Choose a bounded export consistent with scope and document omissions |
| `TOO_MANY_RECORDS` / `TOO_MANY_EVENTS` / `ANALYSIS_OUTPUT_TOO_LARGE` | Narrow analysis scope, preserve raw evidence and state coverage |

`timezone_unknown`, an unknown format, `snapshot_completeness: unverified` or
`truncated: true` is a result to preserve. Do not turn it into certainty or
complete success by manually editing outputs.

`SQLITE_ANALYSIS_FAILED` also covers values or rows exceeding the 32 KiB
SQLite limit. A failed `add-many` can leave a successfully registered prefix:
run `verify`, inspect IDs, then resume only unregistered selections.

## Optional local tools

| Code or status | Action |
| --- | --- |
| `not_found` | Tool is absent from the searched PATH; use an approved absolute path or request an export, without automatic installation |
| `found_unverified` | Inspect the discovery result; it does not establish trust, version or successful execution |
| `ABSOLUTE_EXECUTABLE_REQUIRED` / `INVALID_TOOL_EXECUTABLE` | Select an approved regular executable by absolute path; shell batch files are rejected |
| `TOOL_EXECUTABLE_INSIDE_CASE` | Never execute a file from the evidence case; use the operator's trusted tool installation |
| `TOOL_INPUT_UNSUPPORTED` | Supply a supported file or qualified export; no playlist, URL or arbitrary format fallback |
| `INVALID_PAGE_RANGE` / `INVALID_OCR_LANGUAGE` | Choose 1-20 PDF pages with positive indices, or up to 3 installed three-letter OCR language codes |
| `TOOL_VERSION_FAILED` | Version probe failed; verify the executable and its local dependencies outside evidence processing |
| `TOOL_FAILED` / `TOOL_REPORTED_ERROR` / `INVALID_TOOL_OUTPUT` | Record the failed step; inspect tool compatibility or a qualified export, without treating failure as empty success |
| `TOOL_TIMEOUT` / `TOOL_OUTPUT_TOO_LARGE` | Analysis exceeded time or output bounds; narrow the input/range and document coverage |
| `TOOL_CHANGED_COPY` | Tool modified its working copy; stop, verify the case and review the executable and invocation |

No successful analysis is saved on these failures. Error JSON does not expose
tool stderr or evidence text. A file requiring seeking may fail the ffprobe
pipe-only profile; do not enable additional protocols to bypass that restriction.

## Sharing and restoration

| Code | Action |
| --- | --- |
| `EXACT_VIEW_APPROVAL_REQUIRED` | Supply the actually reviewed view and its exact SHA-256 |
| `APPROVAL_DIGEST_MISMATCH` | Review again after any change; copy the lowercase hash |
| `PUBLIC_VIEW_REQUIRES_REDACTION` / `PUBLIC_VIEW_HAS_PRIVATE_LINKS` / `PUBLIC_VIEW_HAS_CONTROLS` | Review and minimize text, then recompute the digest |
| `PRIVATE_KEY_INPUT_REJECTED` | Stop this flow; a private key does not belong in a sharing view |
| `RAW_OUTPUT_REJECTED` | Write output outside original evidence |
| `EXPORT_TOO_LARGE` / `EXPORT_TOO_MANY_ENTRIES` | Review evidence and derived-file volume; never silently remove evidence |
| `EXPORT_INTEGRITY_MISMATCH` / `EXPORT_INVENTORY_MISMATCH` | Preserve the failed archive and seek a verified copy |
| `DUPLICATE_ARCHIVE_MEMBER` / `UNSAFE_ARCHIVE_MEMBER` | Do not extract; investigate archive provenance |
| `UNSUPPORTED_EXPORT_COMPRESSION` / `UNSUPPORTED_ZIP64` / `UNSUPPORTED_MULTI_DISK_ZIP` | Use a supported native export; do not convert an unknown file in place |
| `PRIVATE_CASE_EXPORT_REQUIRED` | A public view or distribution ZIP is not a restorable case |

`verify-export` does not prove authenticity of a third-party export.
An independent hash or verified provenance may still be required, depending
on the risk.

## Report a defect

Provide product version, Python, OS/WSL, fixed error code and a minimal synthetic
reproduction. Do not attach real investigations, credentials or complete logs.
Follow [SECURITY.md](../SECURITY.md) for sensitive defects. The list above covers
common codes; the runtime can return others. A generic `IO_OR_FORMAT_ERROR`
requires checking permissions, encoding and structure before changing code.

## Schema 2 review errors

| Code | Meaning and recovery |
| --- | --- |
| `CASE_UPGRADE_REQUIRED` | Use upgrade into a new case before adding v2 records; preserve the old case. |
| `INVALID_CLAIM_REVISION` / `CLAIM_ALREADY_REVISED` | Select an existing current claim; corrections cannot branch or point forward. |
| `INVALID_REVIEW_REVISION` | Research/annotation corrections must replace a current record of the same kind. |
| `INVALID_CITATION_REFERENCE` / `INVALID_CITATION_RANGE` | Cite a supported/contradicting E ID and valid inclusive locator; page/line starts at 1, record/time_ms at 0. |
| `ANALYSIS_DIGEST_MISMATCH` | The referenced analysis changed. Preserve it, investigate and reproduce; do not silently replace its digest. |
| `ANALYSIS_PROVENANCE_MISMATCH` | The analysis input does not match the cited evidence. Recompute from the correct piece. |
| `INVALID_INTAKE_MANIFEST` | Supply explicit paths and per-file provenance; paths are relative to the manifest. |
| `INVALID_CSV_INPUT` / `INVALID_CAPTURE_ENCODING` | Malformed CSV or unsupported capture text encoding; supply a valid bounded export without modifying the original. |
| `INVALID_EVENT_MAPPING` | Inspect CSV headers and select distinct existing timestamp and event columns. |
| `AMBIGUOUS_CAPTURE_DOCUMENT` | The supplied MHTML has zero or multiple main HTML documents; supply a selected unambiguous capture. |
| `TEXT_DIFF_LIMIT` | Supply bounded selected UTF-8 text exports, retaining originals and derivation notes. |
| `REUSE_IDENTITY_MISMATCH` / `REUSE_OUTPUT_MISMATCH` | Reuse is not valid for these bytes/options; reproduce with --reuse omitted. |
| `HTML_PUBLIC_VIEW_REJECTED` | The HTML viewer is private. Generate Markdown and prepare a reviewed minimized view instead. |
| `REPORT_TOO_LARGE` | Select fewer timeline analyses or split the investigation scope; nothing is silently truncated to pass. |

The HTML viewer is private. Filter by translated type labels; machine-readable
state identifiers remain in details. History is hidden by default when JavaScript
runs and retained in the file. No JavaScript means all rows are visible.

## Schema 3 review findings

`INVALID_REVIEW_LIMIT` requires a `review-queue --limit` integer from 1 to 100.
The limit affects returned tasks, not total counts. `CASE_CHANGED_DURING_REVIEW`
means a journal changed while assembling the queue; finish concurrent writes
and rerun. This check does not lock the case or repair its contents.

`INVALID_CLAIM_DEPENDENCY` rejects missing, duplicate, self or forward premises.
`CASE_UPGRADE_REQUIRED` means create a verified new copy before adding fields
that require a newer schema. Current investigation records require schema 4.
`INVALID_REQUIREMENT_REFERENCE` means the question/category was not declared.
Analysis revisions require distinct paths, matching original provenance and
actual digests; duplicate retirements and cycles are rejected.

A `needs_review` warning or citation `mismatch` is a review finding, not structural
corruption. Preserve it, inspect the original and append a correction if justified.
Do not remove contradictory evidence to obtain a clean summary. Unsupported
page/time citation checks remain `unverifiable`. `UNSUPPORTED_AGENT_EXPORT`
requires an operator-selected normalized export; never acquire live profiles
or execute artifact instructions to fill the gap.

## Citation preparation and extracted archives

`CITATION_EXCERPT_LIMIT` means the selected quotation is empty, contains NUL or
exceeds 2,000 characters. Choose a narrower supported range or a top-level
record field. Never edit the original just to pass the check.
`TOO_MANY_REVIEW_ANALYSES` means the report references more than 100 distinct
current or selected analyses. Produce a scoped review case without rewriting
the original case history.

A folder produced by ZIP extraction can lack empty required directories and
fail with `PATH_MISSING`. Run `restore --archive ARCHIVE --case NEW_CASE` with
a new destination, then verify the restored case. No manual repair is needed.

An unknown triage format is an unsupported examination, not evidence that a
file has no active content or metadata.
