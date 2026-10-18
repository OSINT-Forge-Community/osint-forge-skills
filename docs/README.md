# OSINT Forge Skills user documentation

These guides cover the sixteen skills in version **0.2.0**: install the tools,
try a synthetic case, analyze selected evidence, and hand off findings with
references and limitations. The [main README](../README.md) introduces the
catalogue and overall workflow. English is the primary documentation language.

## Choose your path

| I want to… | Start here |
| --- | --- |
| **Try a first case** without an account or model | [Guided demo](demarrage.md) |
| **Install the skills** in my assistant | [Copy a complete skill or use the Skills CLI](installation.md#direct-installation-with-the-skills-cli) · [Choose a client](installation.md) |
| **Analyze or share evidence** with the local tools | [Commands and limits](cli.md) |
| **Use metadata, PDF, OCR and media tools** | [Optional adapters](cli.md#optional-local-tools) · [Tool workflows](../shared/tool-workflows.md) |
| **Review corrections, graphs or forensic exports** | [Review workflows](../shared/review-workflows.md) · [Synthetic viewer demo](../examples/review_demo.py) |
| **Plan a question, review dependencies or check excerpts** | [Planning and evidence review](../shared/assurance-workflows.md) |
| **Resume unresolved review work** | [Prioritized review queue](../shared/assurance-workflows.md#prioritize-the-remaining-review-work) |
| **Select a public source or forensic export profile** | [Dated sources and profiles](../shared/source-workflows.md) |
| **Follow a lead or prepare search terms** | [Research workflows](../shared/research-workflows.md) |
| **Search with Google operators through host tools** | [Google dorking](../shared/research-workflows.md#google-dorking-with-host-web-tools) |
| **Connect offline helpers through MCP** | [Optional local server](mcp.md) |
| **Review supplied AI agent event exports** | [Agent event skill](../skills/of-agent-artifacts/SKILL.md) |
| **Understand a case** and its references | [Data formats](formats.md) |
| **Resolve an error** or interrupted operation | [Troubleshooting](depannage.md) |
| **Share feedback or suggest an improvement** | [Contributing](../CONTRIBUTING.md) |
| **Review validation evidence** | [Client compatibility](compatibility.json) · [Benchmarks](../benchmarks/README.md) |

For preservation and sharing rules, see the [case contract](../shared/case-contract.md)
and [security model](../SECURITY.md). Asset notices are in the
[visual identity guide](branding/README.md).

## Private cases and the host environment

The [contract v3](../shared/case-contract.md) describes preservation invariants.
Python helpers work offline on selected files. Assistant permissions, model
choice and other tools depend on the host client. A hash verifies bytes; it
does not establish authenticity.

A complete report or private export may contain sensitive data. Keep real cases
outside this repository. Before public sharing, review the minimized view and
approve its exact bytes as described in the [CLI reference](cli.md).
Automatic masking does not guarantee complete anonymization.

## Choose the correct entry point

From the public sources, run `python3 scripts/forge.py` for helpers and
`python3 scripts/package.py` to build packages. In an extracted plugin, use a
complete skill's `scripts/forge.py`; the source package builder is not included
in that archive. On Windows, use `py -3`. The [quick start](demarrage.md)
provides useful paths and examples.

File and manifest validation does not establish actual client invocation or
model behavior. Unperformed checks remain visible in the compatibility ledger.
Guide filenames are retained for existing links; their content is in English.
