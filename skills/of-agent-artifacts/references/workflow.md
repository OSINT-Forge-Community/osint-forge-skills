# Agent export contract

The helper is an offline interpreter of selected normalized records or an
explicitly selected supported native export. It does not parse every client's
native logs, acquire profiles, inspect MCP
configuration, install agents or send data to a model. The supplied exporter
must be identified by the analyst; the format label does not authenticate it.

JSON uses this object:

```json
{"format":"of-agent-events-v1","events":[{"event_type":"tool_request","call_id":"synthetic-call-1","timestamp":"2026-10-01T10:00:00Z","text":"Requested operation, preserved as data"},{"event_type":"tool_result","call_id":"synthetic-call-1","text":"Reported result, not host-effect proof"}]}
```

JSONL has one event per physical line, each also carrying
`format: of-agent-events-v1`. Blank or malformed lines fail rather than silently
changing source indices. Inputs are UTF-8, at most 4 MiB and 5,000 events.
Text is at most 4,000 characters per event. Preserve the source separately if a
qualified exporter omits or minimizes longer text; do not call that complete.

Event types are `model_text`, `tool_request`, `tool_result`, `host_observation`.
Unknown types remain events with explicit gaps. Unmapped fields stay in the
original and their count is reported. `call_id` links a result only when exactly
one request with that ID exists and precedes its unique result. Duplicate IDs,
missing requests, requests without results, multiple results and missing IDs
remain gaps. No request or result is executed by the helper.

Missing times remain missing; offset-free times remain timezone_unknown.
Every event retains its zero-based source record index and E identifier.
Sorting a later view does not renumber the source. A host observation in the
same export is a supplied assertion until its provenance is independently
reviewed. Use separately supplied audit evidence to test effects, and record
why it corroborates or contradicts the reported result. Temporal correlation
alone is insufficient. `effect_verified` remains false in this parser.

Do not include credentials or unrelated transcript content in reports or model
context. Keep the original private. Use the existing exact-view sharing review
for any eventual public output.

## Selected Codex exec JSONL

Use `--format codex-exec-jsonl` only for a capture of `codex exec --json` stdout
explicitly supplied by the operator. This adapter does not search private
session files or support arbitrary rollout formats. Preserve the original as
one E piece. Add `--exporter-version` when supplied, without treating it as an
authenticated version. No Codex process or model call is started by this parser.

The dated profile `codex-exec-jsonl-2026-10-25` maps selected `item.*` records:
agent messages/reasoning to model statements, started operations to requests
and completed operations to reported results. Command execution, MCP calls,
web searches and file-change records remain claims in the supplied export.
None becomes independent host telemetry. Unrecognized records remain visible.

Physical JSONL line numbers are retained as zero-based `record_index` and
one-based `source_line`. Known thread/turn metadata is omitted from events with
explicit counts and gaps. Unknown fields are counted, never silently treated
as interpreted. Native text over 4,000 characters is clipped with its original
length recorded as a gap, while the original piece remains unchanged. Blank or
malformed lines fail instead of shifting locators. Normalized input remains
strict and rejects oversized text. Export completeness is never inferred.

Profile reference reviewed on 2026-10-25:
[OpenAI non-interactive output documentation](https://learn.chatgpt.com/docs/non-interactive-mode#make-output-machine-readable).
The documented structure guides mapping, not a claim that every client release
or unknown future item type has been qualified.
