# Planning and evidence review

Read the section needed for the current task. Commands are relative to the
loaded skill's `scripts/forge.py`. New cases use schema 3. Schema 1 and 2 remain
readable; `upgrade --case OLD --out NEW` makes a verified copy. Keep OLD intact.
Older readers reject schema 3. No migration or collection runs automatically.

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
PDF pages and millisecond locators remain structurally checked but automatically
unverifiable here. An exact OCR match validates the derived text only. Reports
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
