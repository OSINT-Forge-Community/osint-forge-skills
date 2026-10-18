# Optional local MCP server

The Model Context Protocol interface exposes offline helpers to a host supporting
local `stdio` servers. It uses Python 3.11+ and the standard library. There is no
listening port, remote endpoint, API key, download or provider installation.
Starting a server does not register it in a client.

## Start from the correct location

From a source checkout:

```bash
python3 /absolute/path/osint-forge-skills/scripts/forge.py mcp
```

From a standalone skill or extracted plugin, select a complete skill's helper:

```bash
python3 /absolute/path/of-case-start/scripts/forge.py mcp
```

The process waits for MCP messages on stdin. A compatible host launches and
stops it; closing stdin ends it. On Windows select an absolute Python executable,
or use `py` with `-3` before the script argument.

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

Replace both paths. Configuration locations and schemas belong to the selected
host; this example is not a universal installation command. Add it explicitly
to the intended project or client. No global setting or plugin manifest
automatically enables MCP. Standard skill installation works on its own.

## Tools

| Tool | Arguments | Result |
| --- | --- | --- |
| `forge_plan` | Required `question`, `kinds`; optional `max_steps` | Bounded local plan; host capabilities are not inferred |
| `forge_sources` | Optional `category`, `jurisdiction` | Static dated cards without availability checks |
| `forge_pivots` | Optional `kind` | Six follow-up cards, or one selected card |
| `forge_queries` | Required `kind`, `value`; optional `site` | Three query strings without submitting them |
| `forge_dorks` | Required `phrase`; optional `site`, `filetype`, `exclude` array, `after`, `before` | Google query and encoded search URL; host tools execute the search |
| `forge_verify_case` | No arguments; only with startup `--case` | Byte/reference status and evidence/claim counts |
| `forge_review_summary` | No arguments; only with startup `--case` | Counts of current review items by kind/priority; no task text or identifiers |

Five tools are exposed by default, seven with a startup-selected case.
See [Google dorking](../shared/research-workflows.md#google-dorking-with-host-web-tools) and the
[CLI reference](cli.md#contextual-planning-and-review) for argument values.
Read-only, idempotent and closed-world annotations describe the tools;
enforcement comes from the explicit tool allowlist. No arbitrary commands,
executables, file reads/writes, URL fetches, call replay, model calls or public
exports are exposed.

## Optional case verification and review

Add `"--case", "/absolute/path/selected-private-case"` after `"mcp"` in the
host's args only to enable the two extra tools. The case must already exist.
These tools accept no path argument and cannot select another case. Usual bounded
reads, prohibited paths and symlink checks apply. Results contain counts, status
and verification limits, without filenames, evidence text, claims, URLs or case
paths. Errors use fixed codes. No transcript is written.

`forge_review_summary` counts revised premises, citation issues and gaps in
declared coverage. Full tasks are available only through the local CLI
`review-queue`; the MCP summary omits question/category text and all identifiers.
`no_recorded_gaps` is not a truth, completeness or publication-readiness verdict.
The helper executes no follow-up and changes no case files. It rejects a case
journal change detected during queue assembly with `CASE_CHANGED_DURING_REVIEW`.

Verification reads registered evidence and references; it does not validate
semantic support or authenticity. Large cases can block this sequential server.
Operators control filesystem parents; these checks are not an operating-system
sandbox against a hostile local user. See the [security model](../SECURITY.md).

## Protocol and data control

Supported versions are `2025-11-25` and `2025-06-18`: newline-delimited UTF-8
JSON-RPC over stdio, initialize, initialized notification, ping, tools/list and
tools/call. Unsupported version proposals receive the latest supported version
for negotiation. Other features and HTTP/SSE are not offered. Tools require
completed initialization. Schemas reject unknown fields, invalid types and
out-of-range values. Invalid tool arguments return protocol errors; operational
tool failures return `isError: true`.

Input messages are limited to 65,536 bytes including their newline. An oversized
line returns an error and terminates the process; responses are limited to
262,144 bytes before their newline. Duplicate keys, non-finite JSON constants,
malformed UTF-8 and JSON-RPC batches are rejected. Stdout contains only protocol
messages; startup and IO failures use a fixed stderr code.

An offline server does not make a cloud host or model local: the host may
transmit arguments and responses. Choose client, model and case permissions
independently. Instructions in evidence and tool results remain data.

Implementation references: [MCP transport](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports),
[lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle)
and [tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools).
Automated protocol/subprocess tests are distinct from a real host connection or
model trial. See the [compatibility ledger](compatibility.json) for observations.
