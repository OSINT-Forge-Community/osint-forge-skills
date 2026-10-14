# Contributing

Feedback, bug reports, improvements, suggestions and documentation corrections
are welcome. You do not need to write code to contribute.

## Share feedback through GitHub Issues

Use the repository's [Issues tab](https://github.com/OSINT-Forge-Community/osint-forge-skills/issues)
for public discussion. Check existing issues first and add useful details to
an existing conversation when it covers the same subject.

The repository has [issue labels](https://github.com/OSINT-Forge-Community/osint-forge-skills/labels)
to organize topics. Use a relevant label when GitHub permits it; otherwise
describe the category in the issue so maintainers can label it.

- **Feedback:** describe the task you tried, what helped and what was unclear.
- **Bug reports:** give the skill or command, project/client/tool versions,
  operating system, expected behavior, observed result and minimal steps to
  reproduce. Use synthetic inputs and fixed error codes where possible.
- **Improvements and suggestions:** explain the use case, the current gap and
  the result you would find useful. For a new tool, include its official link,
  local or remote execution requirements and the data it would receive.
- **Documentation:** identify the page or example and suggest clearer wording
  or a corrected command.

Keep real investigations, evidence, personal data, credentials and private
transcripts out of public issues and pull requests. A synthetic reproduction
is preferable to uploading an entire case or unreviewed diagnostic output.

## Security and personal-data concerns

For a security vulnerability or sensitive security report, email
[security@osint-forge.com](mailto:security@osint-forge.com).
Do not publish vulnerability details in an issue; see the
[security reporting guide](SECURITY.md).

For a personal-data concern, use
[privacy@osint-forge.com](mailto:privacy@osint-forge.com).
Keep identifying details out of public issues. Start with a concise description
and relevant context; do not attach credentials or an entire evidence archive.

## Propose a change

For a substantial change, explain the use case in an issue first. Focus a pull
request on one improvement and describe its behavior, checks performed and
remaining limitations. Small corrections can be proposed directly.

Edit the source skills and shared runtime; generate packages with
`python3 scripts/package.py` instead of editing `dist/`. Python helpers remain
standard-library-only and offline. Third-party tools are optional, explicitly
selected and never installed automatically. Preserve originals and use
original synthetic fixtures for examples.

From a source checkout, verify package consistency with
`python3 scripts/package.py --check`. On Windows use `py -3` in place of
`python3`. Describe separately what was tested: package structure, local helper
behavior, a real third-party executable or an actual client/model workflow.
Do not present an unperformed integration trial as passed.

Start with the [documentation](docs/README.md),
[command reference](docs/cli.md) and [case contract](shared/case-contract.md).
