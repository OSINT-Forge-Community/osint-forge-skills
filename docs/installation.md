# Installation on Windows, Linux and WSL

Start with the [main README](../README.md) and
[guided synthetic walkthrough](demarrage.md). The [documentation index](README.md)
includes usage and troubleshooting guides. These commands register or copy
skills; actual discovery/model behavior is tracked separately.

Run Python 3.11+ from this repository and build with `python scripts/package.py`.
The build is offline. In PowerShell use `py -3`; in Linux/WSL use `python3` when
`python` is not mapped. Quote paths with spaces. Install into the filesystem
and user environment used by the target client; Windows and WSL homes differ.

## Native Claude Code plugin

From the built repository or an extracted full distribution:

```text
claude plugin marketplace add .
claude plugin install osint-forge-skills@osint-forge --scope local
claude plugin validate dist/plugins/osint-forge-skills
```

For an extracted full distribution the plugin path is `plugins/osint-forge-skills`.
Restart the session if needed and use `/osint-forge-skills:of-case-start`.
The local scope targets the current project; choose user scope deliberately if
you want all projects. The catalogue resolves paths from its repository root.

## Native Codex plugin

```text
codex plugin marketplace add .
codex plugin add osint-forge-skills@osint-forge
```

Codex CLI 0.162.1 exposes these commands locally. Plugin capabilities and UI
can differ on other versions; use `codex plugin --help` and consult its official
documentation. No config file is edited by our scripts. Registration/installation
changes client settings and is an operator action. Keep a versioned local copy.

## Standalone skills: all four clients

Use an existing explicit target. Default scope is project:

```text
python scripts/install.py install --client opencode --target /path/to/workspace --dry-run
python scripts/install.py install --client opencode --target /path/to/workspace
```

| Client | Project-relative destination | User-relative destination |
| --- | --- | --- |
| Claude | `.claude/skills` | `.claude/skills` |
| Codex | `.agents/skills` | `.agents/skills` |
| OpenCode | `.opencode/skills` | `.config/opencode/skills` |
| Gemini | `.gemini/skills` | `.gemini/skills` |

For `--scope user`, `--target` must explicitly name your actual user home.
The installer never changes environment variables, auth, network permissions
or global model settings. Native plugins and standalone copies are alternatives;
do not install both for the same client/scope.

Select individual skills by repeating `--skill NAME`. Every installed skill
contains its own runtime and case contract. The tool validates all collisions
before copying and records exact installed-file hashes in a local receipt.

Gemini also supports its own native installation:

```text
gemini skills install /absolute/path/dist/plugins/osint-forge-skills/skills/of-case-start --scope workspace
gemini skills list
```

Do not bypass client trust prompts. In OpenCode, discover through its native
skill tool. Compatibility is demonstrated only by the checks actually recorded
in `compatibility.json`; packaging support alone is not a real model trial.

## Remove a standalone installation

```text
python scripts/install.py uninstall --client opencode --target /path/to/workspace --dry-run
python scripts/install.py uninstall --client opencode --target /path/to/workspace
```

All recorded files must be unchanged. A modification blocks the entire removal
so the operator can preserve it. Unrecorded additional files are left intact.
The receipt assumes an operator-controlled target; it is not an authenticated
ownership record against a malicious local user.

For native installations use the client's own uninstall command. This project
does not alter existing plugin registrations during build or testing.

## Official references, checked 2026-10-13

- [Claude plugins](https://code.claude.com/docs/en/plugins)
- [Claude marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Codex local skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenCode skills](https://opencode.ai/docs/skills/)
- [Gemini skills](https://geminicli.com/docs/cli/skills/)
- [Agent Skills format](https://agentskills.io/specification)
