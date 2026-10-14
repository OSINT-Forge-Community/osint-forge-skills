# OSINT Forge Skills user documentation

These guides cover the twelve skills in version **0.1.0**: install the tools,
try a synthetic case, analyze selected evidence, and hand off findings with
references and limitations. The [main README](../README.md) introduces the
catalogue and overall workflow. English is the primary documentation language.

## Choose your path

| Need | Guide | Useful next step |
| --- | --- | --- |
| Install or remove skills in a client | [Installation](installation.md) | [Observed compatibility](compatibility.json) |
| Try the tools without an account or model | [Guided quick start](demarrage.md) | [CLI reference](cli.md) |
| Find arguments, outputs and limits | [Commands](cli.md) | [Troubleshooting](depannage.md) |
| Understand evidence, claims and timestamps | [Data formats](formats.md) | [Contract v1](../shared/case-contract.md) |
| Resume a case after an error | [Troubleshooting](depannage.md) | [Export and restoration](cli.md) |
| Check which clients and platforms were actually verified | [Compatibility](compatibility.json) | [Security limits](../SECURITY.md) |
| Review asset notices | [Identity and provenance](branding/README.md) | [License](../LICENSE), [NOTICE](../NOTICE) |

## Private cases and the host environment

The [contract v1](../shared/case-contract.md) describes preservation invariants.
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
