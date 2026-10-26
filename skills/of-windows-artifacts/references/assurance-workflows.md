# Planning and evidence review

Read the section needed for the current task. Commands are relative to the
loaded skill's `scripts/forge.py`. New cases use schema 4. Schemas 1, 2 and 3 remain
readable; `upgrade --case OLD --out NEW` makes a verified copy. Keep OLD intact.
Older readers reject unsupported schemas. No migration or collection runs automatically.

## Prioritize the remaining review work

Run `review-queue --case CASE --limit 20` when resuming a case or preparing a
report. It checks integrity and returns current claims with revised premises,
incorrect or unsupported citations, missing locators and gaps in declared
source coverage. Each item identifies its references, a suggested skill and
the next check. Load only that skill and the references needed for the task.

Priority 1 covers revised premises, citation mismatches and absent evidence;
priority 2 covers unverifiable citations, critical coverage gaps, absent claims
and undefined coverage; priority 3 covers missing locators and supporting
coverage gaps. These priorities organize work, not confidence or risk scores.
An unavailable source can warrant a documented limitation rather than another
search. Collection and case changes still require their existing scope.

The limit accepts 1-100 items, default 20. `total`, `counts_by_kind` and
`counts_by_priority` cover every item; `shown` and `omitted` explain the returned
slice. Equal-priority items retain deterministic case order. Historical claims
are excluded from the actionable queue but remain subject to integrity checks
and `check-citations`. A missing coverage definition is reported explicitly.
`no_recorded_gaps` is not a completeness, truth or publication-readiness verdict.
This read-only command does not execute its suggestions or change the case.

The optional MCP `forge_review_summary` returns only fixed status labels and
counts for the case selected at server startup. It never exposes queue text,
case paths, evidence IDs, category names or excerpts.

## Plan the next useful check

`plan --kind organization` retains the short route. Repeat `--kind` only to
represent genuinely ambiguous material. A request file supplies the question,
capabilities declared by the operator, authorization already established and
the step budget:

```json
{"question":"Do the supplied filings identify the same company?","kinds":["organization"],"available":["local","search"],"authorized":["local"],"max_steps":2,"deferred_leads":[]}
```

Use `plan --request selected-plan.json --case CASE`. With `--request`, put kinds
in that file or in `--kind`, never both. The output preserves ambiguities,
missing capabilities, deferred leads and the case's review state. It gives a
discriminating check and required input per selected route. This is an advisory
budget; the helper cannot enforce the host agent's tools or permissions.
Availability never authorizes installation, transmission or a broader question.
Stop when the question is answered, the budget is exhausted or no remaining
observation can distinguish the alternatives. Do not repeat established intake.

For media, choose `--media-goal metadata` or `--media-goal geolocation`, or set
`"media_goal":"metadata"` / `"media_goal":"geolocation"` in the JSON request.
This field requires `media` among the kinds. The question is retained as context,
not interpreted to choose a goal. Without a goal, `requires_media_goal` is true
and the media comparison has an `objective_gap` until the operator clarifies it.
Metadata actions examine supplied fields and extraction limits. Geolocation
actions use `of-geolocation` to examine visible cues and competing scenes.
Any new extraction or collection remains a separately authorized host action.

When `available_inputs` is supplied, media comparison requires
`selected_originals`, plus `dated_captures` for geolocation. Local version
comparison requires `selected_originals` without demanding dated captures.
The operator must check that both unchanged versions and any derivation context
are actually available. Input declarations do not verify files or their count.

`selected_skills` retains the material route's method suggestions. `skill_usage`
distinguishes methods assigned to returned actions (`role: action`, with
`action_ids`) from `optional_reference` methods with no returned action.
A budget or resume point can leave a method optional in the current response.
Load it only when the task requires it. An assignment does not mean execution.
Keep completed steps scoped to the same goal. When changing the media goal,
reassess prior work rather than reusing completion declarations automatically.
Recorded case review tasks are recomputed from the case. Their `review:...` IDs
are not accepted in `completed_steps`, which only accepts `KIND:PHASE` IDs.

## Conclusions that depend on other conclusions

Add `claim ... --depends-on C000001` for a premise actually used in the new
claim; repeat for several premises. Direct E support is still required for
observed or inferred claims. Premises must already exist: self references,
forward references and duplicate dependencies are rejected. This ordering
prevents dependency cycles. Dependencies record analyst reasoning, not entailment.

`review-status --case CASE` reports `current`, `historical` or `needs_review`.
When C1 is superseded, C2 depending on C1 and C3 depending on C2 need review.
Their original text, confidence and evidence remain unchanged. Review paths are
shown in Markdown, private HTML and the graph. A current claim has no recorded
revision warning; that status does not establish truth.

A replacement analysis uses a new file, not an overwrite. After registering
both analyses, use `record --input revision.json`:

```json
{"kind":"analysis_revision","previous_analysis":"analysis/first.json","previous_sha256":"ACTUAL_PREVIOUS_DIGEST","replacement_analysis":"analysis/corrected.json","replacement_sha256":"ACTUAL_REPLACEMENT_DIGEST","rationale":"Corrected extraction of the same original piece."}
```

Replace the illustrative digest labels with actual helper/file digests. Both
analyses must resolve to the same input piece and hash; their names must differ.
Repeated retirement and revision cycles are rejected. Citations to the retired
analysis and claims depending on them need review. This does not invalidate the
raw piece. Editing an already cited analysis still fails structural integrity.

## Check excerpts without claiming semantic verification

Use `prepare-citation` from the [recipes](recipes.md#record-a-precise-citation)
to obtain a supported locator and exact quotation before recording a claim.
Inspect each detail of the proposed claim against that excerpt. A generic event
label does not support an identifier, date or ownership relationship by itself.

`check-citations --case CASE` checks registered locators and excerpts. Results:

| Result | Meaning |
| --- | --- |
| `excerpt_found` | The exact quoted excerpt matches the selected range. |
| `locator_found` | The range exists; no quote was supplied for comparison. |
| `mismatch` | Quote, source range or requested field differs. |
| `unverifiable` | The selected format is unsupported or not qualified. |

UTF-8 text lines are one-based. A BOM is removed, Python `splitlines` defines
line boundaries and selected lines are joined by LF. Quotes only normalize CRLF
or CR to LF. Spaces, case, punctuation and Unicode normalization are unchanged.
Record ranges are zero-based and inclusive; they refer to original indices,
including when an event display is sorted. A range is limited to 5,000 records.
Each input is limited to 4 MiB and a check to 5,000 citations.

Raw record citations need `format: csv|json|jsonl`. Add `field` for a top-level
column/key. Without a field, rows are compared using sorted-key JSON with
Unicode retained. JSON input is an array; JSONL has one value per physical line,
with no blank-line skipping. CSV headers must be unique and rows complete.

```json
[{"evidence_id":"E000001","kind":"record","start":0,"end":0,"format":"csv","field":"Description","quote":"Synthetic inventory entry"}]
```

Derived `events` use their original `record_index` and default to field `event`.
Text analyses use `text`, or a string `result` from a qualified tool adapter.
Keep their case-relative analysis path and actual digest in the citation.
Qualified `pdftotext` pages can be checked with exact page coverage. Millisecond
locators can check `timed_transcript` analyses at complete intersecting cue
boundaries. Other page/time formats remain unverifiable. An exact OCR or
transcript match validates the derived text only, never the image or audio. Reports
show the outcomes separately from semantic review; no excerpt text is echoed
by the check command. An analyst must still assess meaning and independence.

## Declare the coverage denominator

Register each question before its searches:

```json
{"kind":"requirement","question_id":"Q1","question":"Was the planned opening implemented?","source_categories":["notice","implementation"],"priority":"critical","rationale":"Implementation evidence could change the conclusion."}
```

Question IDs are unique `Q` plus 1-6 digits, starting above zero. A research
record may reference this question with `question_id` and one declared
`source_category`. Existing unlinked research records remain valid.
`review-status` shows every category, its research IDs and recorded statuses.
Multiple active searches remain visible. One completed query does not erase a
partial one. Revise the relevant R record using `supersedes` when warranted.

Counts apply only to the declared categories. `completed` means a search was
completed, not that an event is absent or a claim established. Preserve
`not_searched`, `no_result`, `partial` and `unavailable`; do not collapse them.

## Keep identities and dates explicit

An entity may include `identifiers: [{"scheme":"synthetic-register","value":"EX-101"}]`,
`jurisdiction` and `candidate_group`. Separate records with different legal
identifiers even if their labels match. A group is a review aid, not a merge.
Relations may state `match_criteria`; they remain candidate or analyst-observed.

Claims and review records may carry `time_context` with `event_time`,
`published_at`, `available_at`, `valid_from` and `valid_until`. Dates and ISO
timestamps remain as supplied, including missing offsets. Acquisition time is
already recorded with the E piece. `available_at` is the analyst's assertion
about when information was available, not a trusted timestamp. Use a claim's
`--time-context dates.json` or put the object in a review record. Compare
validity bounds automatically only when both have normalized offsets.

A historical role is not automatically current. Later-acquired evidence may
revise a conclusion without proving the earlier analyst could have known it.
Graph JSON and GraphML retain these contexts and identifiers as metadata.

## Review the final report

HTML and Markdown reports summarize missing citations, mismatches, unverifiable
excerpts and undefined or incomplete coverage before the findings. The HTML
citation filter includes current claims without a precise citation, including
unconfirmed claims. Historical issues remain visible separately.

Every current claim still needs semantic review even when all excerpts match.
The report cannot determine whether an analyst has completed that review.
Partial-export limits and supplied/total record counts are shown for analyses
cited by current claims or explicitly selected for the HTML timeline, up to 100
unique paths. This does not inventory every unselected analysis in the case.

After the last correction, rerun `check-citations`, `review-queue` and `verify`,
then regenerate the report before exporting. Disclose remaining gaps rather
than weakening checks to obtain an empty queue.
