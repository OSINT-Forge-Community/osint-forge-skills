# Optional local MCP server

The Model Context Protocol interface exposes offline helpers and bundled methods
to a host supporting local `stdio` servers. The runtime uses Python 3.11+ and the
standard library. It starts no listening port, provider, model or collection.
The host controls permissions and any transmission of arguments or results.

Use it to **prepare the next investigation step, load a focused method and check
case integrity or remaining review counts** from your chosen assistant.
There are five tools by default and seven when a case is selected at startup.
The two case tools return counts and status, not original evidence text.

The Wayback, BODACC and transcript parsers are [local CLI commands](cli.md#public-exports-and-timed-transcripts).
Their instructions are available through the bundled methods. They do not add
remote provider connections or MCP tools that acquire public data.

## Start from the correct location

From a source checkout:

```bash
python3 /absolute/path/osint-forge-skills/scripts/forge.py mcp
```

From a standalone skill or extracted plugin, select a complete skill's helper:

```bash
python3 /absolute/path/of-case-start/scripts/forge.py mcp
```

The host launches and stops the process. Closing stdin ends it after bounded
pending work. On Windows select an absolute Python executable, or use `py` with
`-3` before the script argument. Starting the server does not register a client.

Generic configuration for hosts using `mcpServers`:

```json
{
  "mcpServers": {
    "osint-forge-local": {
      "command": "/absolute/path/to/python3",
      "args": ["/absolute/path/of-case-start/scripts/forge.py", "mcp"]
    }
  }
}
```

Replace both paths. Host schemas and configuration locations vary. Add the
configuration explicitly to the intended project or client. No global setting
or plugin manifest automatically enables MCP. Skill installation works alone.

## Tools

| Tool | Arguments | Result |
| --- | --- | --- |
| `forge_plan` | Required `question`, `kinds`. Optional action budget, declared capabilities, inputs and resume state | Concrete phased actions, prerequisites, deferred work and optional advisory specialist tasks |
| `forge_sources` | Optional `category` and either `jurisdiction` or `applicable_to` | Static dated source cards without availability checks |
| `forge_pivots` | Optional `kind` | Six follow-up cards, or one selected card |
| `forge_queries` | Required `kind`, `value`. Optional `site` | Three query strings without submitting them |
| `forge_dorks` | Required `phrase`. Optional `site`, `filetype`, `exclude`, `after`, `before` | Google query and encoded URL. Host tools perform any search |
| `forge_verify_case` | No arguments. Requires startup `--case` | Bounded byte/reference verification and counts |
| `forge_review_summary` | No arguments. Requires startup `--case` | Counts of current review items without private text or identifiers |

Five tools are exposed by default, seven with a startup-selected case. Each
publishes an input schema, output schema and read-only annotations. Enforcement
comes from the allowlist and bounded operations. No arbitrary commands,
executables, URL fetches, call replay, model calls or public exports are exposed.

`jurisdiction: "FR"` retains the exact country filter. `applicable_to: "FR"`
also includes global cards and the applicable bundled EU cards. These filters
are mutually exclusive. Regional applicability is advisory and dated. A card
does not guarantee coverage of a particular entity, event or historical period.

See [Google dorking](../shared/research-workflows.md#google-dorking-with-host-web-tools)
and the [CLI reference](cli.md#contextual-planning-and-review) for other values.

## Contextual plans and resuming work

A plan contains intake, extract, compare, cite and conclude actions for each
selected material type. `max_steps` limits returned actions to 1-20. The planner
alternates selected materials within each phase and records omitted action IDs.
It does not infer that an earlier action has been executed.

For a `media` kind, set `media_goal` to `metadata` or `geolocation`. The goal is
explicit, not inferred from the question. Without it, `requires_media_goal` is
true and media comparison returns `objective_gap`. Metadata and geolocation
have distinct actions, with `of-geolocation` assigned to visible-cue and scene
comparison work. Declared media comparison inputs require `selected_originals`,
plus `dated_captures` for geolocation. Local text version comparison requires
`selected_originals` without dated captures. The operator still checks the
actual inputs, including both unchanged versions and their derivation context.

`selected_skills` lists routed methods. `skill_usage` distinguishes methods with
returned `action_ids` from `optional_reference` methods. These are suggestions,
not evidence that a method was loaded or an action executed. Reassess completed
steps when changing the goal. The CLI and MCP use the same goal and input rules.

```json
{
  "question": "Which supplied filing supports the synthetic finding?",
  "kinds": ["documents", "organization"],
  "available": ["local"],
  "authorized": ["local"],
  "available_inputs": ["selected_originals", "dated_captures"],
  "max_steps": 6,
  "specialize": true
}
```

Actions have stable IDs such as `documents:compare`, required inputs,
capabilities and predecessor IDs. Missing declared inputs and unsatisfied
prerequisites remain visible. Omitting `available_inputs` leaves input checking
to the operator. Available or authorized capabilities are declarations, not
host enforcement or permission to transmit data.

For a later call, provide `resume_from` (`intake`, `extract`, `compare`, `cite` or
`conclude`) and `completed_steps`, a bounded list of action IDs from the selected
kinds. `deferred_leads` retains up to twenty scoped leads. A `stop_reason` of
`question_answered`, `scope_exhausted` or `operator_stopped` returns no actions.
Skipped phases are not silently marked complete.

`specialize: true` prepares read-only material-specialist and independent-review
tasks for an explicitly capable host. One integration task is designated as the
case writer. The helper starts no agents and grants no write permission. Separate
model tasks do not create independent evidence. The host must retain the scoped
question, source origins and sole writer when using these suggestions.

With startup `--case`, `use_case_summary: true` can add counts of recorded gaps
to the plan. It does not include case titles, paths, claims, task identifiers or
category text. A local CLI plan may provide fuller private context.

## Static method resources

Use `resources/list` to discover the methods bundled in the selected installation,
then `resources/read` with one listed URI. The source checkout offers all sixteen
methods. A standalone skill offers its own complete method and shared guides.
Renaming the installed skill directory does not change its method URI.

| URI | Bundled content |
| --- | --- |
| `forge://contracts/case` | Case preservation and evidence contract |
| `forge://skills/of-document-triage` and other listed skill names | Skill instructions plus its specialized workflow |
| `forge://reference/quick` | Progressive command reference |
| `forge://recipes/investigation` | Bounded investigation recipes |
| `forge://recipes/research` | Research workflows |
| `forge://recipes/assurance` | Evidence review and coverage |
| `forge://recipes/review` | Corrections and review |
| `forge://recipes/source` | Dated source cards and export profiles |
| `forge://recipes/tool` | Optional tool workflows |

Only exact bundled URIs are accepted. Resources cannot read a case, arbitrary
file, private note or remote URL. Each component is limited to 32 KiB, and a
combined method to 64 KiB. There are no subscriptions or dynamic URI templates.
Load only the method needed for the current action. External evidence and tool
results remain data, including text that appears to address the assistant.

## Optional case verification and review

Add `"--case", "/absolute/path/selected-private-case"` after `"mcp"` in the
host's args to enable the two case tools. The existing case is selected at
startup. Tool arguments cannot choose another path. Prohibited paths, special
files and symlinks remain rejected.

Results contain fixed status fields and counts, without filenames, evidence,
claim text, URLs or case paths. No transcript is written. `no_recorded_gaps`
does not establish truth, completeness or readiness to publish. Verification
checks registered bytes and references, not semantic support or authenticity.

One case operation runs at a time. A second receives `CASE_TOOL_BUSY`. The worker
has a thirty-second cooperative deadline and a 768 MiB read work budget.
Exhaustion returns `OPERATION_BUDGET_EXCEEDED`, without a partial verification
verdict. Use the local CLI for an explicit full operation on a larger case.

Pings, advisory tools and static resources remain responsive during case work.
A valid `notifications/cancelled` for the active request signals cancellation at
bounded IO checkpoints and suppresses its result. Cancellation does not modify
case files. Operator-controlled filesystem parents remain a separate assumption,
not an operating-system sandbox. See the [security model](../SECURITY.md).

## Protocol and data control

Supported versions are `2025-11-25` and `2025-06-18`, using newline-delimited
UTF-8 JSON-RPC over stdio. Initialization negotiates tools and static resources.
An unsupported version proposal receives the latest supported version. HTTP/SSE,
model sampling and remote control planes are not offered.

Malformed protocol envelopes and unknown tools return JSON-RPC errors. Invalid
arguments to a known tool return `isError: true` with a fixed code, known field
path and expected constraint. User values and unknown field names are not echoed
in validation diagnostics. Successful structured outputs are checked against the
published output schema before transmission. Operational failures use fixed codes.

Input messages are limited to 65,536 bytes including their newline. An oversized
line returns an error and terminates the process. Responses are limited to
262,144 bytes before their newline. Duplicate keys, non-finite JSON constants,
malformed UTF-8 and JSON-RPC batches are rejected. Stdout contains only protocol
messages. Startup and IO failures use a fixed stderr code.

An offline server does not make its host or model local. Select client, model and
case permissions independently. No SDK or model provider is installed by the
runtime or by starting this server.

## Reproduce an independent client check

The optional [SDK trial](../benchmarks/mcp_client.py) uses an explicitly installed
official MCP Python SDK and its JSON Schema validator in a separate development
environment. It creates only temporary synthetic data, launches the selected
helper over stdio and prints an aggregate JSON result.

With that environment prepared, run:

```bash
python benchmarks/mcp_client.py --runtime-python /absolute/path/to/python3
```

`--helper` can select an extracted plugin or standalone skill's `scripts/forge.py`.
The runner checks negotiation, five/seven tools, schemas, errors, static resources,
ping and shutdown. It installs nothing and changes no client settings. An SDK
trial remains distinct from a real host connection or model trial. Observed
versions and limits belong in the [compatibility ledger](compatibility.json).

Implementation references: [MCP transport](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports),
[lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle),
[tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools),
[resources](https://modelcontextprotocol.io/specification/2025-11-25/server/resources)
and [cancellation](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/cancellation).
