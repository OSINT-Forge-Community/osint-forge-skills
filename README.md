<p align="center">
 <img src="assets/readme-banner.en.png" alt="Silex the lynx and Rivet the automaton investigate a copper clue." width="100%">
</p>

<h1 align="center">OSINT Forge Skills</h1>

<p align="center">
 <strong>Investigate, verify and hand off the evidence.</strong><br>
 16 open-source OSINT &amp; forensic skills with local tools.<br>
 Claude Code · Codex · OpenCode · Gemini CLI
</p>

<p align="center">
 <a href="VERSION"><img src="https://img.shields.io/badge/Version-0.3.0-965D31?style=flat&amp;labelColor=24292F&amp;logo=github&amp;logoColor=white" alt="Version 0.3.0"></a>
 <a href="#the-skills"><img src="https://img.shields.io/badge/Skills-16-64748B?style=flat&amp;labelColor=24292F" alt="16 Skills"></a>
 <a href="#tools-you-can-use"><img src="https://img.shields.io/badge/Optional_Tools-4-786452?style=flat&amp;labelColor=24292F" alt="4 Optional Tools"></a>
 <a href="docs/installation.md"><img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat&amp;labelColor=24292F&amp;logo=python&amp;logoColor=white" alt="Python 3.11+"></a>
 <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache--2.0-5C6670?style=flat&amp;labelColor=24292F" alt="Software License: Apache-2.0"></a>
</p>

<p align="center">
 <a href="README.fr.md">Français</a> · <a href="#start-in-five-minutes">Quick start</a> · <a href="#tools-you-can-use">Tools</a> · <a href="#search-with-google-dorking">Dorking</a> · <a href="#the-skills">16 skills</a> · <a href="#benchmarks">Benchmarks</a>
</p>

Turn selected sources into a case you can review, resume and hand off.
**OSINT Forge Skills combines investigation methods, local analysis tools and
an optional MCP server** for analysts, investigators and people learning OSINT.
Preserve originals, document competing explanations and produce findings with
references another person can check.

The skills, Python runtime and documentation are **free and open source under
Apache-2.0**. Local helpers need no account, API key or paid service. Choose your
own assistant and model, whose access and costs remain separate.

## Why use OSINT Forge Skills?

| Your advantage | What the project provides |
| --- | --- |
| **Revisit every finding** | Preserved originals, source references and citations to pages, lines, records or complete subtitle intervals |
| **Keep uncertainty visible** | Alternative hypotheses, contradictory evidence, source-origin review and explicit gaps |
| **Resume with a clear next step** | Phased plans, a prioritized review queue and correction history without erasing earlier findings |
| **Keep control of your tools** | Offline Python standard library, no runtime telemetry and no mandatory provider or automatic tool installation |
| **Hand off usable work** | Private searchable HTML reports in English/French, verified case export/restore, GraphML and Timesketch-field CSV |

![Preserve selected evidence, examine sources and contradictions, share a reviewed report.](assets/workflow.en.svg)

## What you can do

| Your starting point | What you can produce |
| --- | --- |
| **A Wayback CDX index** | A dated selection of capture entries for an exact URL, with original row references. Compare separately supplied page captures. |
| **A BODACC JSON export** | A publication history by SIREN, separating publication dates from declared act dates and identifying partial exports. |
| **SRT or WebVTT subtitles** | Referenced passages with cue intervals, source lines and declared transcription/translation context. |
| **Documents, logs and browser or Windows exports** | File triage, timelines and evidence-linked observations with unsupported formats made explicit. |
| **Supplied publications or agent traces** | Source comparisons, documented contradictions and reported actions separated from verified effects. |

These workflows analyze selected files locally. Archive retrieval, registry
queries and other web research use separately authorized host tools. Subtitle
checks verify stored text, not spoken words. [Formats and commands](docs/cli.md).

<a id="start-in-five-minutes"></a>

## Try a case

From the source repository or the complete extracted plugin root, with
**Python 3.11+** and a new output directory:

```bash
mkdir -p cases
python3 examples/public_imports_demo.py --out cases/public-imports-demo
```

Open **`cases/public-imports-demo/case/reports/report.en.html`**.
The synthetic demo includes a Wayback index, a BODACC export and subtitles,
checks **three citations**, then exports and restores the private case.
No model, account or network access is required.

<details>
<summary>Windows / PowerShell and other demos</summary>

```powershell
New-Item -ItemType Directory -Force .\cases | Out-Null
py -3 examples/public_imports_demo.py --out .\cases\public-imports-demo
```

| Demo | Try it for |
| --- | --- |
| [First case](docs/demarrage.md#full-demo-from-source) | Seven evidence items, two claims and a shared publication origin |
| [Corrections and visual review](docs/demarrage.md#review-a-corrected-case-visually) | History, annotated events, candidate relations and exchange formats |
| [Dependencies and citations](docs/demarrage.md#review-dependencies-and-citations) | Conclusions needing review and an intentionally mismatched quote |

These are scripted examples made from original synthetic material. They do not
measure a model's investigation quality.

</details>

<a id="tools-you-can-use"></a>

## What is included

| Component | What you get |
| --- | --- |
| **16 skills** | Investigation methods, focused workflows and evidence-handling rules for your assistant |
| **Forge CLI** | Local intake, parsing, comparison, review, reports and portable case exports |
| **Optional MCP stdio** | Five planning/research tools, bundled method resources and two count-only tools for a startup-selected case |
| **Four optional adapters** | ExifTool for metadata, pdftotext for PDF text, Tesseract for OCR and ffprobe for media metadata |

Each complete skill folder contains its runtime, guides, license and notice.
Optional executables are installed and selected by you. Their results retain
the source hash, tool version and arguments. [Tool workflows](shared/tool-workflows.md)
· [CLI reference](docs/cli.md) · [MCP setup](docs/mcp.md).

## Search with Google dorking

Prepare targeted queries locally, then run them with your assistant's authorized
web tools. Dated source cards and six pivot workflows help choose the next check.
The runtime does not submit searches or collect pages.

```bash
python3 scripts/forge.py dorks --phrase "Harbor Example Ltd" --site example.org --filetype pdf
```

The example uses a fictional organization and a reserved domain.
[Search workflow and operators](shared/research-workflows.md#google-dorking-with-host-web-tools).

<details>
<summary>Research workflow and technical components</summary>

![Prepare a query locally, search through authorized host tools, then preserve selected sources.](assets/search-workflow.en.svg)

## What powers the project

![Offline Forge core, optional local tools and host-controlled assistant capabilities.](assets/toolkit.en.svg)

The runtime and workflows are original. Reviewed research approaches inform
some methods without bundling third-party OSINT runtimes or services.
[References and attribution](shared/research-workflows.md#design-references).

</details>

<a id="install-in-your-ai-assistant"></a>

## Connect your assistant

[Copy a complete skill or use the Skills CLI](docs/installation.md#direct-installation-with-the-skills-cli).
Build native plugin archives from source with `python3 scripts/package.py`.

| Claude Code | Codex | OpenCode · Gemini CLI |
| :---: | :---: | :---: |
| [Native plugin](docs/installation.md#native-claude-code-plugin) | [Native plugin](docs/installation.md#native-codex-plugin) | [Standalone skills](docs/installation.md#standalone-skills-all-four-clients) |

> Use of-case-start on these supplied documents. Preserve the originals,
> examine contradictions and prepare a referenced report. Keep unknowns explicit.

Installation routes and observed client trials are documented separately.
[Compatibility record](docs/compatibility.json).

<a id="the-12-skills"></a>
<a id="the-skills"></a>

## Pick your investigation stage

| Stage | Skills |
| --- | --- |
| **Scope** | [Case start](skills/of-case-start/SKILL.md) |
| **Check sources** | [Provenance](skills/of-source-provenance/SKILL.md) · [Domains](skills/of-domain-infrastructure/SKILL.md) · [Organizations](skills/of-organization-research/SKILL.md) · [Geolocation](skills/of-geolocation/SKILL.md) |
| **Examine files** | [Documents](skills/of-document-triage/SKILL.md) · [Media](skills/of-media-forensics/SKILL.md) · [Browser history](skills/of-browser-artifacts/SKILL.md) · [Windows exports](skills/of-windows-artifacts/SKILL.md) · [Agent event exports](skills/of-agent-artifacts/SKILL.md) |
| **Test explanations** | [Timeline](skills/of-log-timeline/SKILL.md) · [Correlation](skills/of-evidence-correlate/SKILL.md) · [Hypotheses](skills/of-hypothesis-audit/SKILL.md) · [Version comparison](skills/of-version-compare/SKILL.md) |
| **Hand off** | [Report](skills/of-investigation-report/SKILL.md) · [Export](skills/of-case-export/SKILL.md) |

<a id="what-has-been-verified"></a>
<a id="benchmarks"></a>

## Tests & benchmarks

**October 26, 2026, runtime snapshot `271ca22`: 296 tests passed on Linux/WSL,
including 22 public-export and transcript tests.** All 16 generated skills and
682 distribution files were checked. The new demo ran from the extracted plugin,
and all three new commands ran from an extracted standalone skill in isolated Python.

The package version remains **0.3.0**, with the latest additions listed under
**Unreleased** in the [changelog](CHANGELOG.md). Cases use schema **4**.

- Earlier official MCP SDK checks passed. Selected native Windows suites also
  passed on the October 25 snapshot, with two symlink skips per Python version.
- Historical client/model pilots remain available with their exact scope.
  They do not establish a general gain in accuracy, speed or token cost.
- Live provider APIs, full client/platform coverage, general prompt-injection
  resistance and audio accuracy are not established by these local tests.

[Reproduce a demo and read the results](benchmarks/README.md)
· [Dated compatibility and limits](docs/compatibility.json).

**Before using real evidence:** your host controls what a remote model receives.
Hashes check bytes, not authenticity. Review exports before sharing. Masking
alone does not guarantee anonymization. [Security](SECURITY.md).

## Help shape the project

[Open an issue](https://github.com/OSINT-Forge-Community/osint-forge-skills/issues)
for feedback, a reproducible bug or a proposed workflow.
[Contribution guide](CONTRIBUTING.md).

Security: [security@osint-forge.com](mailto:security@osint-forge.com)<br>
Personal data: [privacy@osint-forge.com](mailto:privacy@osint-forge.com)

---

[Documentation](docs/README.md) · [CLI](docs/cli.md) · [Troubleshooting](docs/depannage.md) · [Package version](VERSION) · [Changelog](CHANGELOG.md)

Software, skills and text: **[Apache-2.0](LICENSE)** · [NOTICE](NOTICE).<br>
Visuals © OSINT Forge, all rights reserved. [Asset provenance](docs/branding/README.md).<br>
Silex and Rivet are promotional mascots. Client names imply no affiliation or endorsement.
