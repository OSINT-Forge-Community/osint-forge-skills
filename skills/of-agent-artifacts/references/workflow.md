# Agent export contract

The helper is an offline interpreter of selected, operator-normalized records.
It does not parse every client's native logs, acquire profiles, inspect MCP
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
one request with that ID exists and precedes it. Duplicate IDs, missing requests
and missing IDs remain gaps. No request or result is executed by the helper.

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
