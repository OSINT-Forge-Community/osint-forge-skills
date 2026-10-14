# Case contract v1

The bundled utility runs without network access or optional Python packages.
Use `python scripts/forge.py --help` relative to the loaded skill directory.
On Windows, `py -3` is an equivalent launcher. Quote every user-supplied path.
The authoring repository also exposes `python scripts/forge.py` at its root.

## Private case layout

- `case.json`: schema version 1, scope, title and creation time.
- `evidence.jsonl`: stable E000001 identifiers, relative raw paths, SHA-256,
  size, original basename, acquisition time, optional HTTPS source URL and
  analyst origin label. A label never establishes source independence.
- `claims.jsonl`: stable C000001 identifiers; text; `supports` and `contradicts`
  evidence IDs; `observed`, `inferred` or `unconfirmed` state; qualitative
  confidence; rationale containing assumptions, limitations and what would
  distinguish competing explanations.
- `raw/`: exact private copies of explicitly selected source files.
- `analysis/`, `reports/`, `exports/`: derived local outputs.

Register files with `add`; never manufacture evidence records by hand. Source
files must be outside the case. `verify` checks registered bytes and reference
structure, not semantic truth or authenticity. An observed/inferred claim needs
support. Unconfirmed claims must have low confidence. High confidence with an
unresolved contradicting piece is rejected. Do not remove a contradiction just
to pass a validator: retain it and revise the conclusion.

Reports are private by default. Raw names, URLs and hashes can be sensitive.
Do not paste raw evidence, profiles, credentials or whole transcripts into a
remote model. Prepare a minimized view and confirm the host's data policy.
These helpers constrain their own IO, not the host model, shell or network.

## Time and provenance

Keep source time and acquisition time separate. ISO timestamps with an explicit
offset can be normalized to UTC; missing offsets remain `timezone_unknown`.
Never use the workstation timezone as an implicit answer. Browser event epochs
are decoded by their documented format; clock accuracy remains unverified.
UTC values outside the representable year range remain `invalid` events.
Chronologies compare instants, including fractional seconds, with stable ties.
Browser outputs preserve exact URLs up to 16 KiB with `url_exact: true`;
correlation skips legacy URLs lacking this marker. Regenerate those analyses.

`provenance` groups identical bytes and supplied origin labels transitively.
Other groups remain candidates with unknown independence. Record evidence for
editorial ownership, upstream attribution and publication chronology separately.
Different domains, models or hashes do not establish independent confirmation.

## Limits and recovery

Maximum file: 64 MiB. Maximum raw case: 256 MiB. Structured records/output:
4 MiB. Event limit: 5,000. Runtime has no acquisition, sandbox, EXIF decoder,
PDF text parser, binary EVTX parser, malware execution or authenticity detector.
Use an already approved local tool or request a trusted export for these formats;
never install a provider or tool as a silent fallback.
Browser SQLite values/rows are bounded to 32 KiB inside SQLite, URLs to 16 KiB
and titles to 8 KiB of UTF-8. Oversize fields or cumulative output are rejected;
display titles over 1,000 characters have `title_truncated: true`.

`add` makes bounded copies; symlinks, special files and known SQLite WAL
sidecars are rejected. Use a stable copy or coherent SQLite backup produced by
the operator. Even a WAL-free snapshot has unverified completeness. Keep parent
directories under the operator's control; helpers are not a filesystem sandbox.
Windows file ACLs require separate operator control; POSIX modes alone do not
prove NTFS confidentiality.

For many selected files, `add-many` holds one case lock and verifies all raw
bytes before and after the batch. Each successful addition commits separately.
If a later source fails, completed additions remain; run `verify` and inspect
the journal before resuming. Do not blindly replay the whole batch. The optional
URL and origin label apply to every file in the batch. There is no directory crawl.

Errors are JSON with fixed codes and exit status 2. An interrupted update can
leave an unindexed raw file or `.forge.lock`; stop and inspect with the operator.
Do not reset manifests, delete originals or auto-remove another process's lock.

## Sharing and portability

`export --mode private` includes original pieces. Treat its ZIP as confidential.
`verify-export` checks archive members and hashes without extracting. `restore`
accepts only a verified private export, creates a new case and rechecks it.
Keep the independently recorded ZIP hash if detecting manifest rewriting matters.
Hashes inside the same writable archive are not signatures or trusted timestamps.

`prepare-share` masks some credentials, email addresses and IPv4 addresses,
removes private raw links and hashes, and returns `review_required`. It does not
find every name, address, identifier or sensitive inference. Review the exact
view with the human; then `export --mode public --view ... --approved-sha256 ...`
binds the export to its approved bytes. The digest is operator-supplied, not a
cryptographically authenticated human approval. Any edit changes it and blocks
export. Public bundles contain the reviewed view and its export manifest only.

## Commands

```text
init --case CASE --title TITLE --scope SCOPE
add --case CASE --source FILE [--url HTTPS_URL] [--origin-group LABEL]
add-many --case CASE --source FILE --source OTHER_FILE [--url HTTPS_URL] [--origin-group LABEL]
claim --case CASE --text TEXT --state observed|inferred|unconfirmed
      --rationale TEXT [--support E000001] [--contradict E000002]
      [--confidence low|medium|high]
verify --case CASE
provenance --case CASE
triage --case CASE --evidence E000001 --out CASE/analysis/triage.json
timeline --case CASE --evidence E000001 --format json|jsonl|csv
         --out CASE/analysis/timeline.json [--csv CASE/analysis/timeline.csv]
browser --case CASE --evidence E000001 --out CASE/analysis/browser.json
correlate --case CASE --input CASE/analysis/a.json --input CASE/analysis/b.json
          --out CASE/analysis/correlation.json
report --case CASE --lang en|fr [--replace]
prepare-share --input FILE --out NEW_FILE
export --case CASE --mode private --out NEW_ARCHIVE
export --case CASE --mode public --view REVIEWED_FILE
       --approved-sha256 DIGEST --out NEW_ARCHIVE
verify-export --archive ARCHIVE
restore --archive PRIVATE_ARCHIVE --case NEW_CASE
doctor
```
