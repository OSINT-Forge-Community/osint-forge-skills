# Review and exchange workflows

These commands are included in each generated skill. Prefix them with
`python scripts/forge.py` from the loaded skill. All examples are synthetic.
New cases use schema 3. Read schema 1 and 2 cases normally; use
`upgrade --case OLD --out NEW` before adding newer record semantics. It preserves OLD.

## Select a workflow

`plan --kind organization` suggests relevant skills without loading or executing
them. Other kinds: documents, media, domain, versions, windows-export, browser,
logs, agent-export. Load one skill at a time and only the reference needed at that step.
The plan is a suggestion, not authorization for network activity or installation.
Record missing capabilities and stop when further evidence would not discriminate
the hypotheses or the authorized scope is exhausted.

## Precise citations and corrections

Pass `claim --citations citations.json` alongside the existing support/contradict
arguments. The file is an array:

```json
[{"evidence_id":"E000001","kind":"line","start":2,"end":3,"quote":"Synthetic quoted passage"}]
```

Kinds: page and line are one-based; record and time_ms are zero-based.
Ranges include both endpoints. Locators and excerpts are analyst assertions;
the helper checks structure, not whether an excerpt supports a conclusion.
For a derived analysis, add `analysis` (a flat case-relative path such as
`analysis/events.json`) and its actual `sha256`. Verification checks the digest
and original E reference. Do not invent a digest or label OCR as original text.

`claim ... --supersedes C000001` appends a correction. Only an existing current
claim may be replaced; branching corrections and forward references are rejected.
The historical claim remains intact. Cite the correction's evidence again.

## Research coverage

`record --case CASE --input research.json` appends an R record:

```json
{"kind":"research","question":"Was the notice implemented?","query":"Supplied notices for Dock 7","scope":"Selected October extracts only","tool":"manual review","status":"partial","evidence":["E000001"],"rationale":"The implementation log was not supplied."}
```

Statuses: not_searched, no_result, partial, unavailable, completed. A completed
search is not a proven conclusion. A no_result records the query and its scope;
it never proves universal absence. Revise research with `supersedes: R...`.
Never record credentials or unrelated identifiers in queries.

## Entities and relations

```json
{"kind":"entity","entity_type":"organization","label":"Harbor Example Ltd","evidence":["E000001"],"rationale":"Named in the supplied synthetic register."}
```

Entity types: organization, person, domain, document, location, account, asset.
Create separate records for unresolved namesakes. No automatic merge occurs.

```json
{"kind":"relation","source":"R000001","target":"R000002","label":"reported operator","state":"candidate","evidence":["E000001"],"rationale":"Relationship requires a second filing; valid only for the recorded period."}
```

Both endpoints must be existing entities. State is candidate or observed.
`graph --case CASE --format graphml --out CASE/analysis/relations.graphml`
exports evidence, claims and relations. JSON is also supported. Exported edges
retain evidence IDs and status. No claim of compatibility with a particular
Maltego, OGI or Aleph version follows from a well-formed GraphML file.

## Timelines and annotations

`import-events --case CASE --evidence E000001 --time-field TimeCreated
--event-field Description --out CASE/analysis/events.json` maps a supplied CSV.
Headers must be unique. Original row indices survive sorting. Additional columns
remain in the original evidence and are listed as unmapped.

Annotations use `record` with kind annotation, analysis path, its actual sha256,
record_index, tags (up to 20 short ASCII labels), note and rationale. The referenced
event must exist. Revise with supersedes; annotate the original index, not the
sorted display position.

`export-events --case CASE --input analysis/events.json
--out CASE/analysis/timesketch.csv` exports only normalized times. Keep the returned
omission count and loss description with the CSV. Missing or ambiguous times are
not guessed. Original analyses and annotations remain authoritative for review.

## Private local viewer

`report --case CASE --format html --lang fr --input analysis/events.json`
creates `reports/report.fr.html`. Repeat --input for up to 20 analyses. Open it
locally: no server, CDN or network is required. The review dashboard separates
preserved evidence, current claims, claims affected by revisions and current
claims with citation issues. Select a review card or filter to examine revised
premises, mismatched or unverifiable citations, or uncertain event times. These
are review prompts, not credibility scores. Search supports multiple words and
accent-insensitive matching across recorded text and details; type and history
filters apply only to the records section.

Declared coverage retains each source category and its separate research states.
A completed search does not erase a partial search or prove absence. Citation
checks show exact-excerpt, locator, mismatch and unverifiable outcomes, including
marked historical claims; they do not establish semantic support. Original
record details, current event annotations and a bounded relation diagram remain
available. Large graphs remain available through the graph export.

The responsive English/French view supports system, light and dark appearance.
Search and appearance choices remain in the page; nothing is stored or sent.
Printing includes all records and history regardless of screen filters. Without
JavaScript all rows remain visible and interactive controls are disabled. The
HTML is a private review artifact, not a minimized public view. Use the Markdown
prepare-share/export procedure for public sharing.

## Captures and version changes

`capture --case CASE --evidence E000001 --format mhtml
--out CASE/analysis/capture.json` extracts inert text from one main HTML part.
UTF-8 HTML is also supported. No resource is fetched and no script is executed.
This is not browser rendering or acquisition authenticity verification.

`compare --case CASE --left E000001 --right E000002
--out CASE/analysis/changes.json` compares UTF-8 text, capped at 200,000 bytes
and 1,000 lines per version. Order is chosen by the analyst, not inferred.

## Batch intake and explicit reuse

`intake --case CASE --manifest selected.json` accepts
`{"files":[{"path":"notice.txt","source_url":"https://example.invalid/notice","origin_group":"bulletin"}]}`.
Paths are relative to the manifest's directory and cannot escape it. Each file
has its own provenance. A failure preserves the committed prefix; verify and
resume only remaining files. No directory scan is performed.

`tool-run ... --reuse analysis/previous.json` checks input identity, executable
bytes, observed version, arguments and stored output consistency. It still probes
the executable version. Reuse is marked explicitly and is not a fresh execution
or independent corroboration. Omit --reuse to reproduce the analysis. A local
actor able to rewrite an analysis can also rewrite its hashes; reproduce when
the analysis is untrusted. System libraries and trained OCR data are not hashed.

For contextual plans, dependency warnings, citations, requirements and dated
identity context, read the shared assurance workflow. Source selection and
forensic-export profiles are in the shared source workflow.
