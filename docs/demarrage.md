# Guided quick start

This walkthrough uses only the original synthetic corpus. No account, token,
model or network access is needed to try the helpers.
[Installation in a client](installation.md) is a separate step.

## Choose the right environment

| What you have | Available command | Purpose |
| --- | --- | --- |
| Source repository | `python3 scripts/forge.py` | Use helpers and build packages |
| Extracted plugin | `python3 skills/of-case-start/scripts/forge.py`, from the plugin root | Use the included runtime |
| Extracted standalone skill | `python3 scripts/forge.py`, from its directory | Use that skill and its runtime |

In Windows PowerShell, replace `python3` with `py -3`. Install the client and
its skills in the same environment: Windows and WSL have different home
directories. Use Python 3.11+ and quote paths.

## Full demo from source

Choose a **new** output directory outside the repository, with an existing
parent. The script refuses to replace a previous demo.

```bash
python3 scripts/forge.py doctor
python3 scripts/demo.py --out '/tmp/forge-demo-resume-01'
python3 scripts/forge.py verify --case '/tmp/forge-demo-resume-01/case'
python3 scripts/forge.py verify --case '/tmp/forge-demo-resume-01/resumed-case'
```

Equivalent PowerShell example, if your temporary directory exists and the
chosen name is unused:

```powershell
py -3 scripts/forge.py doctor
py -3 scripts/demo.py --out "$env:TEMP\forge-demo-resume-01"
py -3 scripts/forge.py verify --case "$env:TEMP\forge-demo-resume-01\case"
py -3 scripts/forge.py verify --case "$env:TEMP\forge-demo-resume-01\resumed-case"
```

The expected result has seven pieces of evidence, two claims, two uncertain
timestamps and a verified restoration. The script prepares a view for review
but does not create a public export without human review. `summary.json`
preserves these statuses.

Next, open `case/reports/report.en.md` and `case/analysis/timeline.json`.
The three articles repeat the same attribution; they do not count as three
independent witnesses. A stated time without a timezone remains uncertain.
The hostile file is passive data. This walkthrough demonstrates the helpers,
not a model's resistance to prompt injection.

## Create a small case manually

Run these commands at the source repository root. `/tmp` is an existing parent
on Linux/WSL; choose an equivalent path on Windows. The case name must be unused.

```bash
python3 scripts/forge.py init --case '/tmp/forge-manual-01' --title 'Review of synthetic sources' --scope 'Supplied corpus only; no external collection'
python3 scripts/forge.py add --case '/tmp/forge-manual-01' --source 'examples/inputs/article-a.json' --origin-group 'harbor-bulletin'
python3 scripts/forge.py add --case '/tmp/forge-manual-01' --source 'examples/inputs/article-b.json' --origin-group 'harbor-bulletin'
python3 scripts/forge.py claim --case '/tmp/forge-manual-01' --text 'Both captures attribute their announcement to the Harbor Bulletin.' --state observed --support E000001 --support E000002 --confidence medium --rationale 'Observation of capture text; the actual closure and publisher independence are not established.'
python3 scripts/forge.py provenance --case '/tmp/forge-manual-01'
python3 scripts/forge.py verify --case '/tmp/forge-manual-01'
python3 scripts/forge.py report --case '/tmp/forge-manual-01' --lang en
python3 scripts/forge.py export --case '/tmp/forge-manual-01' --mode private --out '/tmp/forge-manual-01/exports/private.zip'
python3 scripts/forge.py verify-export --archive '/tmp/forge-manual-01/exports/private.zip'
python3 scripts/forge.py restore --archive '/tmp/forge-manual-01/exports/private.zip' --case '/tmp/forge-manual-resumed-01'
```

`E000001` and `E000002` assume a new case populated in this order. In an existing
case, use the IDs returned by `add`. A valid hash establishes preservation of
registered bytes, not the truth of an announcement. Private exports contain
originals and remain confidential.

## Move to an assistant

Build packages, then choose a native or standalone installation in the
[installation guide](installation.md). Example initial request:

> Use of-case-start on the supplied synthetic fixtures. Define the scope,
> create a new local case outside the repository and verify the evidence.
> Keep unknowns explicit, distinguish copies of a shared source and identify
> the commands actually executed. No external collection for this trial.

Invocation commands differ by client. Read the client's help and observe
actual discovery. Files in a recognized directory alone do not establish
validated integration.

Next steps: [CLI reference](cli.md), [data formats](formats.md),
[troubleshooting](depannage.md) and [compatibility](compatibility.json).

## Review a corrected case visually

From the public checkout or complete extracted plugin, choose a new directory:

```bash
python3 examples/review_demo.py --out cases/review-demo
```

Open `cases/review-demo/case/reports/report.en.html` (or report.fr.html) locally.
Filter conclusions, evidence, research and events; enable History to inspect
the replaced claim. The example includes a candidate organization relationship,
a missing timezone and a CSV exchange with one omitted uncertain event.
The generator also verifies a private export and restores a copy. Everything
is original synthetic material; no model, account or network is involved.
[Review command examples](../shared/review-workflows.md).
