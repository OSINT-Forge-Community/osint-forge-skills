# Command reference

This reference describes helper version **0.1.0**. The [contract v1](../shared/case-contract.md)
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
The helper checks structure, not citation relevance. V1 appends claims but
has no revision or deletion command. Document corrections in new claims;
preserve the history.

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
outputs simplify V1 private exports, which include only files directly
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

| V1 limit | Value |
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
