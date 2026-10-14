#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from package import expected_files

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
from forgekit.safeio import (ForgeError, atomic_write, digest, json_bytes, read_bytes,
                            read_json, relative_path, require, safe_path)


def prefix(client: str, scope: str) -> str:
    project = {"claude": ".claude/skills", "codex": ".agents/skills",
               "opencode": ".opencode/skills", "gemini": ".gemini/skills"}
    require(client in project and scope in ("project", "user"), "INVALID_INSTALL_TARGET")
    return ".config/opencode/skills" if client == "opencode" and scope == "user" else project[client]


def install(target: str | Path, client: str, scope: str, selected: list[str] | None = None,
            dry_run: bool = False) -> dict:
    base = safe_path(target)
    require(base.is_dir(), "DIRECTORY_REQUIRED")
    destination = prefix(client, scope)
    receipt = base / ".osint-forge-skills" / f"{client}-{scope}.json"
    safe_path(receipt, exists=False)
    require(not receipt.exists(), "INSTALL_ALREADY_EXISTS")
    generated = expected_files()
    start = "plugins/osint-forge-skills/skills/"
    available = sorted({name[len(start):].split("/")[0] for name in generated if name.startswith(start)})
    skills = available if not selected else sorted(set(selected))
    require(bool(skills) and all(name in available for name in skills), "UNKNOWN_SKILL")
    files = {destination + "/" + name[len(start):]: data
             for name, data in generated.items()
             if name.startswith(start) and name[len(start):].split("/")[0] in skills}
    for skill in skills:
        path = safe_path(base / destination / skill, exists=False)
        require(not path.exists(), "SKILL_COLLISION")
    if dry_run:
        return {"status": "dry_run", "client": client, "scope": scope,
                "skills": skills, "file_count": len(files), "changed_files": 0}
    created = []
    try:
        for name, data in sorted(files.items()):
            path = safe_path(base / name, exists=False)
            safe_path(path.parent, exists=False)
            path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(path, data)
            created.append((path, digest(data)))
        receipt.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(receipt, json_bytes({"schema_version": 1, "client": client, "scope": scope,
            "skills": skills, "files": [{"path": name, "sha256": digest(data)}
                                        for name, data in sorted(files.items())]}))
    except BaseException:
        for path, expected in reversed(created):
            if path.exists() and not path.is_symlink() and digest(read_bytes(path)) == expected:
                path.unlink()
        raise
    return {"status": "installed", "client": client, "scope": scope,
            "skills": skills, "file_count": len(files)}


def uninstall(target: str | Path, client: str, scope: str, dry_run: bool = False) -> dict:
    base = safe_path(target)
    destination = prefix(client, scope)
    receipt_path = safe_path(base / ".osint-forge-skills" / f"{client}-{scope}.json")
    receipt = read_json(receipt_path)
    require(isinstance(receipt, dict) and receipt.get("schema_version") == 1
            and receipt.get("client") == client and receipt.get("scope") == scope,
            "INVALID_INSTALL_RECEIPT")
    generated = expected_files()
    start = "plugins/osint-forge-skills/skills/"
    allowed = {destination + "/" + name[len(start):]
               for name in generated if name.startswith(start)}
    rows = receipt.get("files")
    require(isinstance(rows, list) and bool(rows), "INVALID_INSTALL_RECEIPT")
    names = []
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get("path"), str), "INVALID_INSTALL_RECEIPT")
        name = relative_path(row["path"])
        require(name in allowed and name not in names, "INVALID_INSTALL_RECEIPT")
        names.append(name)
        path = safe_path(base / name)
        require(digest(read_bytes(path)) == row.get("sha256"), "INSTALLED_FILE_MODIFIED")
    if dry_run:
        return {"status": "dry_run", "file_count": len(names), "changed_files": 0}
    parents = set()
    for name in names:
        path = safe_path(base / name)
        path.unlink()
        parents.update(parent for parent in path.parents
                       if parent != base and parent.is_relative_to(base / destination))
    for parent in sorted(parents, key=lambda path: len(path.parts), reverse=True):
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
    receipt_path.unlink()
    return {"status": "uninstalled", "removed_files": len(names)}


def main():
    parser = argparse.ArgumentParser(description='Optional offline standalone installation; native plugins are documented separately.')
    parser.add_argument("action", choices=("install", "uninstall"))
    parser.add_argument("--client", choices=("claude", "codex", "opencode", "gemini"), required=True)
    parser.add_argument("--target", required=True, help="Explicit existing project or user home directory")
    parser.add_argument("--scope", choices=("project", "user"), default="project")
    parser.add_argument("--skill", action="append", help="Install selected self-contained skills")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "install":
            result = install(args.target, args.client, args.scope, args.skill, args.dry_run)
        else:
            require(not args.skill, "UNINSTALL_USES_RECEIPT")
            result = uninstall(args.target, args.client, args.scope, args.dry_run)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ForgeError, OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "code": str(exc) if isinstance(exc, ForgeError) else "INSTALL_IO_ERROR"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
