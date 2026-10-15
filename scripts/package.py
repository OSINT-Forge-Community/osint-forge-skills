#!/usr/bin/env python3

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
from forgekit.safeio import ForgeError, atomic_write, json_bytes, read_bytes, require, safe_path

PUBLIC_DOCUMENTS = (
    "README.md", "installation.md", "demarrage.md", "cli.md", "formats.md",
    "depannage.md", "compatibility.json", "branding/README.md",
    "branding/provenance.json",
)
PUBLIC_BENCHMARKS = (
    "results/2026-10-15-assurance-model/results.json",
    "results/2026-10-15-assurance-model/source-manifest.json",
    "review.py", "results/2026-10-14-review-cli/results.json",
    "results/2026-10-14-review-cli/source-manifest.json",
    "results/2026-10-14-review-integration/results.json",
    "results/2026-10-14-review-model/results.json",
    "results/2026-10-14-review-model/source-manifest.json",

    "README.md", "runtime.py", "results/2026-10-14-runtime/results.json",
    "results/2026-10-14-runtime/source-manifest.json",
    "results/2026-10-14-runtime-cleanup/results.json",
    "results/2026-10-14-runtime-cleanup/source-manifest.json",
    "skillsbench_codex.py",
    "results/2026-10-14-skillsbench/results.json",
    "results/2026-10-14-skillsbench/protocol.json",
    "results/2026-10-14-skillsbench/skill-source-manifest.json",
    "results/2026-10-14-skillsbench/requirements.txt",
)


def collect(directory: Path, *, release: bool = False) -> dict[str, bytes]:
    result = {}
    safe_path(directory)
    for path in sorted(directory.rglob("*")):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        safe_path(path)
        if path.is_dir():
            continue
        require(path.suffix in (".py", ".md", ".json", ".yaml", ".csv", ".txt", ".svg", ".png", ".jpg")
                or path.name in ("LICENSE", "NOTICE")
                or release and (path.suffix == ".zip" or path.name in ("LICENSE", "NOTICE", "VERSION", "SHA256SUMS")),
                "UNEXPECTED_PACKAGE_INPUT")
        require(not any(part in (".git", ".codex", ".claude", "envs", "cases")
                        for part in path.relative_to(directory).parts), "UNEXPECTED_PACKAGE_INPUT")
        result[path.relative_to(directory).as_posix()] = read_bytes(path)
    return result


def skill_resources() -> dict[str, bytes]:
    files = {"scripts/forgekit/" + name: data
             for name, data in collect(ROOT / "shared" / "forgekit").items()
             if name.endswith(".py")}
    for name in ("case-contract.md", "tool-workflows.md", "review-workflows.md",
                 "assurance-workflows.md", "source-workflows.md"):
        files["references/" + name] = read_bytes(ROOT / "shared" / name)
    for name in ("LICENSE", "NOTICE"):
        files[name] = read_bytes(ROOT / name)
    return files


def skill_sources(check: bool = False) -> tuple[dict[str, bytes], dict[Path, dict[str, bytes]]]:
    resources = skill_resources()
    sources = {}
    folders = sorted(safe_path(ROOT / "skills").iterdir())
    for folder in folders:
        require(safe_path(folder).is_dir(), "INVALID_SKILL_ENTRY")
    with ThreadPoolExecutor(max_workers=4) as reader:
        for folder, source in zip(folders, reader.map(collect, folders)):
            actual = {name: data for name, data in source.items()
                      if name in resources or name.startswith("scripts/forgekit/")}
            require(set(actual) <= set(resources), "UNEXPECTED_SKILL_FILE")
            if check:
                require(actual == resources, "SKILL_RESOURCE_DRIFT")
            sources[folder] = source
    return resources, sources


def sync_skills(check: bool = False) -> dict:
    resources, sources = skill_sources(check)
    updates = {}
    for folder, source in sources.items():
        for name, data in resources.items():
            if source.get(name) != data:
                target = safe_path(folder / name, exists=False)
                if not check and target.exists():
                    require(target.is_file() and target.stat().st_nlink == 1, "UNSAFE_OUTPUT_FILE")
                updates[target] = data
    if not check:
        for target, data in updates.items():
            safe_path(target.parent, exists=False).mkdir(parents=True, exist_ok=True)
            atomic_write(target, data, replace=target.exists())
    return {"status": "verified" if check else "synchronized", "skills": len(sources),
            "resource_files": len(resources) * len(sources), "changed_files": len(updates),
            "network_calls": False}


def archive(members: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as result:
        for name, content in sorted(members.items()):
            info = zipfile.ZipInfo(name, (2000, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            result.writestr(info, content)
    return output.getvalue()


def expected_files() -> dict[str, bytes]:
    _, sources = skill_sources(check=True)
    identity = json.loads(read_bytes(ROOT / "plugin.json"))
    name, version = identity["name"], identity["version"]
    require(version == (ROOT / "VERSION").read_text().strip(), "VERSION_MISMATCH")
    plugin = "plugins/" + name + "/"
    files = {plugin + "plugin.json": json_bytes(identity)}
    metadata = {key: identity[key] for key in ("name", "version", "description", "author", "license")}
    files[plugin + ".claude-plugin/plugin.json"] = json_bytes(metadata)
    files[plugin + ".codex-plugin/plugin.json"] = json_bytes({**metadata, "skills": "./skills/"})
    contract = read_bytes(ROOT / "shared" / "case-contract.md")
    tool_workflows = read_bytes(ROOT / "shared" / "tool-workflows.md")
    review_workflows = read_bytes(ROOT / "shared" / "review-workflows.md")
    review_controls = {name: read_bytes(ROOT / "shared" / name) for name in ("assurance-workflows.md", "source-workflows.md")}
    skill_archives = {}
    for folder, source in sources.items():
        for path, content in source.items():
            files[plugin + "skills/" + folder.name + "/" + path] = content
        skill_archives[f"skills/{folder.name}-{version}.zip"] = archive({
            folder.name + "/" + path: content for path, content in source.items()})
    for name in ("LICENSE", "NOTICE", "README.md", "README.fr.md", "README.en.md", "VERSION",
                 "SECURITY.md", "CHANGELOG.md", "CONTRIBUTING.md"):
        files[plugin + name] = read_bytes(ROOT / name)
    for relative, data in collect(ROOT / "assets").items():
        files[plugin + "assets/" + relative] = data
    files[plugin + "shared/case-contract.md"] = contract
    files[plugin + "shared/tool-workflows.md"] = tool_workflows
    files[plugin + "shared/review-workflows.md"] = review_workflows
    for name, data in review_controls.items():
        files[plugin + "shared/" + name] = data
    for relative in PUBLIC_DOCUMENTS:
        files[plugin + "docs/" + relative] = read_bytes(ROOT / "docs" / relative)
    for relative in PUBLIC_BENCHMARKS:
        files[plugin + "benchmarks/" + relative] = read_bytes(ROOT / "benchmarks" / relative)
    for relative, data in collect(ROOT / "examples").items():
        files[plugin + "examples/" + relative] = data
    for relative in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        catalog = json.loads(read_bytes(ROOT / relative))
        entry = catalog["plugins"][0]
        if relative.startswith(".claude-plugin"):
            entry["source"] = "./plugins/" + identity["name"]
        else:
            entry["source"]["path"] = "./plugins/" + identity["name"]
        files[relative] = json_bytes(catalog)
    files["README.md"] = ("![OSINT Forge Skills](plugins/osint-forge-skills/assets/readme-banner.en.png)\n\n"
        "# OSINT Forge Skills distribution " + version + "\n\n"
        "16 skills for evidence-based investigation, with self-contained local tools.\n"
        "This marketplace is already built. Start from this extracted directory.\n\n"
        "## Choose your next step\n\n"
        "| I want to… | Guide |\n"
        "| --- | --- |\n"
        "| Understand the workflow | [Overview](plugins/osint-forge-skills/README.md) |\n"
        "| Read in French | [Présentation](plugins/osint-forge-skills/README.fr.md) |\n"
        "| Install in Claude Code | [Native plugin](plugins/osint-forge-skills/docs/installation.md#native-claude-code-plugin) |\n"
        "| Install in Codex | [Native plugin](plugins/osint-forge-skills/docs/installation.md#native-codex-plugin) |\n"
        "| Install in OpenCode or Gemini | [Standalone skills](plugins/osint-forge-skills/docs/installation.md#standalone-skills-all-four-clients) |\n"
        "| Use the local tools | [Package entry points](plugins/osint-forge-skills/docs/demarrage.md#choose-the-right-environment) |\n\n"
        "The complete plugin is in `plugins/osint-forge-skills/`. Each skill\n"
        "includes its own offline Python runtime; Python 3.11+ is required.\n"
        "Standalone installation from an archive is covered in the installation guide.\n\n"
        "## Validation and data control\n\n"
        "[Recorded compatibility](plugins/osint-forge-skills/docs/compatibility.json) ·\n"
        "[Helper benchmarks](plugins/osint-forge-skills/benchmarks/README.md)\n\n"
        "Codex pilots and observed reads of selected project skills are recorded\n"
        "in the benchmark guide. Full catalogue coverage and other clients remain unevaluated. Client setup\n"
        "is an explicit operator action. A remote assistant may transmit what it reads.\n\n"
        "[Documentation](plugins/osint-forge-skills/docs/README.md) ·\n"
        "[License](plugins/osint-forge-skills/LICENSE)\n").encode()
    files.update(skill_archives)
    files[f"osint-forge-skills-{version}.zip"] = archive({
        path: content for path, content in files.items() if not path.startswith("skills/")})
    files["SHA256SUMS"] = "".join(
        hashlib.sha256(content).hexdigest() + "  " + path + "\n"
        for path, content in sorted(files.items()) if path.endswith(".zip")).encode()
    return files


def build(check: bool = False) -> dict:
    if not check:
        sync_skills()
    files = expected_files()
    destination = safe_path(ROOT / "dist", exists=False)
    if check:
        actual = collect(destination, release=True)
        require(actual == files, "PACKAGE_DRIFT")
    else:
        if destination.exists():
            actual = collect(destination, release=True)
            require(set(actual) <= set(files), "UNEXPECTED_BUILD_FILE")
        else:
            destination.mkdir(mode=0o700)
        for relative, data in files.items():
            target = destination / relative
            safe_path(target.parent, exists=False)
            target.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(target, data, replace=target.exists())
    return {"status": "verified" if check else "built", "skills": len(list((ROOT / "skills").iterdir())),
            "files": len(files), "version": (ROOT / "VERSION").read_text().strip(), "network_calls": False}


def main():
    parser = argparse.ArgumentParser(description='Synchronize standalone skills and build reproducible local packages.')
    parser.add_argument("--check", action="store_true", help="Check generated skills and packages without writing")
    parser.add_argument("--sync-skills", action="store_true", help="Only synchronize skill resources; combine with --check to verify")
    args = parser.parse_args()
    try:
        result = sync_skills(args.check) if args.sync_skills else build(args.check)
        print(json.dumps(result, sort_keys=True))
    except (ForgeError, OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "code": str(exc) if isinstance(exc, ForgeError) else "BUILD_IO_ERROR"}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
