<p align="center">
 <img src="assets/readme-banner.en.png" alt="Silex the lynx and Rivet the automaton investigate a copper clue." width="100%">
</p>

<h1 align="center">OSINT Forge Skills</h1>

<p align="center">
 <strong>From sources to findings. Keep the evidence.</strong><br>
 15 OSINT &amp; forensic skills for AI assistants.<br>
 Claude Code · Codex · OpenCode · Gemini CLI
</p>

<p align="center">
 <a href="VERSION"><img src="https://img.shields.io/badge/Version-0.1.4-965D31?style=flat&amp;labelColor=24292F&amp;logo=github&amp;logoColor=white" alt="Version 0.1.4"></a>
 <a href="#the-skills"><img src="https://img.shields.io/badge/Skills-15-64748B?style=flat&amp;labelColor=24292F" alt="15 Skills"></a>
 <a href="#tools-you-can-use"><img src="https://img.shields.io/badge/Optional_Tools-4-786452?style=flat&amp;labelColor=24292F" alt="4 Optional Tools"></a>
 <a href="docs/installation.md"><img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat&amp;labelColor=24292F&amp;logo=python&amp;logoColor=white" alt="Python 3.11+"></a>
 <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache--2.0-5C6670?style=flat&amp;labelColor=24292F" alt="Software License: Apache-2.0"></a>
</p>

<p align="center">
 <a href="README.fr.md">Français</a> · <a href="#start-in-five-minutes">Quick start</a> · <a href="#tools-you-can-use">Tools</a> · <a href="#the-skills">15 skills</a> · <a href="#benchmarks">Benchmarks</a>
</p>

Documents, source captures, logs and browser-history exports become a portable
case with preserved evidence, referenced findings and explicit unknowns.
You choose the assistant and model; the included Python tools work offline.

![Preserve selected evidence, examine sources and contradictions, share a reviewed report.](assets/workflow.en.svg)

<a id="start-in-five-minutes"></a>

## Try a case

From the source repository root, with **Python 3.11+**. No account or API key needed.

```bash
mkdir -p cases
python3 scripts/demo.py --out cases/demo
```

<details>
<summary>Windows / PowerShell</summary>

```powershell
New-Item -ItemType Directory -Force .\cases | Out-Null
py -3 scripts/demo.py --out .\cases\demo
```

</details>

Use a **new** output directory. Open `cases/demo/case/reports/report.en.md`.
The offline demo registers **7 evidence items and 2 claims**, then verifies an
export and restoration. [Walkthrough →](docs/demarrage.md)

> **Three articles. One original source.** In the synthetic Dock 7 case,
> three articles repeat the same bulletin; the event's exact time stays unknown.
> These findings are scripted, not discovered by a model. [Explore the case](examples/PROVENANCE.md).

**Review a corrected case visually:** run
`python3 examples/review_demo.py --out cases/review-demo`, then open
`cases/review-demo/case/reports/report.en.html`. The synthetic example includes
precise references, correction history, research gaps, annotated events and
candidate relations. [Review and exchange guide](shared/review-workflows.md).

<a id="tools-you-can-use"></a>

## Tools at your fingertips

| Tool | Use it for |
| --- | --- |
| **Forge · included** | Preserve evidence, triage files, build timelines, correlate and export |
| **ExifTool · optional** | PNG, JPEG and PDF metadata |
| **pdftotext · optional** | Text from selected PDF pages |
| **Tesseract · optional** | OCR on PNG/JPEG images |
| **ffprobe · optional** | Audio/video container and stream metadata |

```bash
python3 scripts/forge.py tools
python3 scripts/forge.py plan --kind organization
```

Four adapters are included; **install and select the external executables yourself**.
Saved results retain the source hash, tool version, arguments and output.
Batch intake keeps each file's provenance. Review supplied HTML/MHTML, compare
text versions, map forensic CSV and export GraphML or Timesketch-field CSV.
Explicit result reuse is labelled separately from a fresh tool execution.
Web search, DNS/RDAP and maps depend on your client's available, authorized tools.
[Commands & limits](docs/cli.md#optional-local-tools) · [Tool workflows](shared/tool-workflows.md)

<a id="install-in-your-ai-assistant"></a>

## Connect your assistant

Build with `python3 scripts/package.py`, then install from `dist/`:

| Claude Code | Codex | OpenCode · Gemini CLI |
| :---: | :---: | :---: |
| [Native plugin](docs/installation.md#native-claude-code-plugin) | [Native plugin](docs/installation.md#native-codex-plugin) | [Standalone skills](docs/installation.md#standalone-skills-all-four-clients) |

> Use `of-case-start` on these supplied documents, without network requests.
> Check source independence, examine contradictions and prepare a referenced report.

<a id="the-12-skills"></a>
<a id="the-skills"></a>

## Pick your investigation stage

| Stage | Skills |
| --- | --- |
| **Scope** | [Case start](skills/of-case-start/SKILL.md) |
| **Check sources** | [Provenance](skills/of-source-provenance/SKILL.md) · [Domains](skills/of-domain-infrastructure/SKILL.md) · [Organizations](skills/of-organization-research/SKILL.md) · [Geolocation](skills/of-geolocation/SKILL.md) |
| **Examine files** | [Documents](skills/of-document-triage/SKILL.md) · [Media](skills/of-media-forensics/SKILL.md) · [Browser history](skills/of-browser-artifacts/SKILL.md) · [Windows exports](skills/of-windows-artifacts/SKILL.md) |
| **Test explanations** | [Timeline](skills/of-log-timeline/SKILL.md) · [Correlation](skills/of-evidence-correlate/SKILL.md) · [Hypotheses](skills/of-hypothesis-audit/SKILL.md) · [Version comparison](skills/of-version-compare/SKILL.md) |
| **Hand off** | [Report](skills/of-investigation-report/SKILL.md) · [Export](skills/of-case-export/SKILL.md) |

<a id="what-has-been-verified"></a>
<a id="benchmarks"></a>

## Tests & benchmarks

Recorded on **October 14, 2026**: **117 tests passed** on Linux/WSL, including
**15 synthetic adapter tests**. [Benchmarks and real trials →](benchmarks/README.md)

<details>
<summary>What these checks cover, and what remains untested</summary>

- 15 standalone runtimes, 4 installation adapters, demo export and restoration.
- Four real forensic binaries and the EN/FR HTML viewer passed synthetic Linux container trials.
- Six Codex review sessions completed; selected project skills were read in all three
  sessions using them. Both conditions produced accepted assessments; no quality gain is demonstrated.
- Historical offline and SkillsBench results remain available with their limitations.
- Full catalogue/client coverage, general investigation quality, prompt-injection resistance,
  native Windows/macOS and real third-party application imports remain unvalidated.
- Manifest observations are dated in the [compatibility ledger](docs/compatibility.json).
  Historical results apply to their recorded source snapshots.

</details>

**Before using real evidence:** a remote assistant may transmit what it reads.
Hashes check bytes, not authenticity. Review exports before sharing; masking
is not guaranteed anonymization. [Security](SECURITY.md) · [Supported formats & limits](docs/cli.md#capabilities-and-limits)

## Help shape the project

Ideas, bugs or improvements? **[Open an issue](https://github.com/OSINT-Forge-Community/osint-forge-skills/issues)**
and choose a label. [Contribution guide](CONTRIBUTING.md)

Security: [security@osint-forge.com](mailto:security@osint-forge.com)<br>
Personal data: [privacy@osint-forge.com](mailto:privacy@osint-forge.com)

---

[Documentation](docs/README.md) · [CLI](docs/cli.md) · [Troubleshooting](docs/depannage.md) · [Package version](VERSION) · [Changelog](CHANGELOG.md)

Software, skills and text: **[Apache-2.0](LICENSE)** · [NOTICE](NOTICE).<br>
Visuals © OSINT Forge, all rights reserved. [Asset provenance](docs/branding/README.md).<br>
Silex and Rivet are promotional mascots. Client names imply no affiliation or endorsement.
