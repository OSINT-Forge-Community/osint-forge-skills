# Security model and reporting

Threat impact: medium. Selected files, databases, event text and model-facing
documents can be hostile. Helpers reject symlinks and special files, bound
size/record counts, separate raw/derived IO, neutralize output controls, use
fixed read-only SQLite queries, and never run samples or make network calls.

The explicit `tool-run` command executes an operator-selected third-party tool,
never an evidence executable. It passes a temporary copy, fixed argument lists
without a shell, a restricted environment and bounded stdout/stderr/time.
ExifTool default config loading is disabled; ffprobe reads selected bytes via
the pipe protocol with a fixed recognized demuxer. No tool installation or web
lookup is performed. Host search/browser/DNS tools remain separately governed.

External binaries are not sandboxed by this wrapper. Their memory use, general
filesystem access and all descendant processes on every OS are not bounded by
these checks. Use trusted, maintained executables and suitable host isolation
for hostile inputs. Detection on PATH is not trust or vulnerability validation.
Temporary-copy timestamps differ from original acquisition metadata; output
is untrusted and can contain personal data or instructions to ignore.

These controls are not a sandbox or protection against a compromised OS/client.
Keep case parents, executables and install receipts under operator control.
Concurrent hostile directory replacement and privileged local attackers are
outside the utility's trust boundary. Enforce host permissions independently.

Private cases and exports contain original content. Heuristic masking is not
anonymization. Human review must cover names, locations, identifiers, sensitive
context and unrecognized credentials before approving the exact public view.
Do not provide credentials or real sensitive samples with a report.

Sovereignty impact: autonomous local content and utilities. Interoperability
adapters are files, with no model API, provider SDK or background collection.
A chosen cloud client retains its external control plane and data policy; the
project does not classify it as sovereign or approve its use for private data.

## Report a security issue

Send security vulnerabilities and sensitive security reports to
[security@osint-forge.com](mailto:security@osint-forge.com).
Include the affected version or commit, impact, relevant fixed error codes and
minimal synthetic reproduction steps. Do not send credentials, real evidence
archives or private transcripts. Keep vulnerability details out of public issues.

For a personal-data concern, use
[privacy@osint-forge.com](mailto:privacy@osint-forge.com).
Describe the concern privately without posting identifying details on GitHub.

General feedback, non-sensitive bugs and suggestions belong in
[GitHub Issues](https://github.com/OSINT-Forge-Community/osint-forge-skills/issues).
See [Contributing](CONTRIBUTING.md) for reporting guidance and issue labels.

## Private review views and schema 2

The local HTML viewer escapes supplied text and uses a hash-based Content
Security Policy for its bundled script/style. It loads no external resources.
Filters hide rows visually, not from the file: the entire HTML remains private.
HTML documents/scripts are refused by prepare-share and public export; prepare
a minimized Markdown view instead. This is not a general HTML sanitizer.

Schema 2 citations and review records check references and bind selected derived
analyses by digest. They do not authenticate an analyst, timestamp or logical
conclusion. A person able to rewrite all case files can recompute hashes.
Explicit tool-result reuse checks consistency but is not independent reproduction.
HTML/MHTML extraction never executes the page; hostile parsing remains bounded
by input/output limits and should use an appropriate isolated environment.

## Optional MCP boundary

The local stdio MCP server exposes an explicit read-only tool allowlist with
bounded messages and validated arguments. It opens no network listener and
executes no arbitrary commands. Without startup `--case`, no case operation is
available. With one selected case, verification returns only counts, status and
limits; tool calls cannot select another path. It creates no transcript.
Filesystem parents and host permissions remain operator-controlled. A remote
host/model may still receive tool arguments and results; local MCP does not
approve that transmission. See [MCP setup](docs/mcp.md) for the protocol scope.
