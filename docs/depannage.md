# Troubleshooting and error recovery

Start by recording the **command, fixed code and step**, without copying private
evidence. Avoid repeating a mutation without knowing its outcome. `verify`
and `verify-export` are the first read-only checks. Never resolve a preservation
error by deleting the journal or original evidence. The helper performs no
automatic recovery.

## Installation and builds

| Code or symptom | Cause to check | Action |
| --- | --- | --- |
| Python missing or too old | Interpreter in the current shell | Use Python 3.11+; `py -3` on Windows or `python3` on Linux/WSL |
| `PATH_MISSING` / `DIRECTORY_REQUIRED` | Missing parent, target or source | Check path and current directory; create only the intended parent |
| `PACKAGE_DRIFT` | `dist/` no longer matches sources | Review changes, rebuild with `scripts/package.py`, then run `--check` |
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
| `FILE_TOO_LARGE` / `CASE_TOO_LARGE` / `STRUCTURED_INPUT_TOO_LARGE` | Choose a bounded export consistent with scope and document omissions |
| `TOO_MANY_RECORDS` / `TOO_MANY_EVENTS` / `ANALYSIS_OUTPUT_TOO_LARGE` | Narrow analysis scope, preserve raw evidence and state coverage |

`timezone_unknown`, an unknown format, `snapshot_completeness: unverified` or
`truncated: true` is a result to preserve. Do not turn it into certainty or
complete success by manually editing outputs.

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
