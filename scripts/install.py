#!/usr/bin/env python3

from __future__ import annotations

import argparse
from contextlib import contextmanager, nullcontext
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys

from package import installation_files

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
from forgekit.safeio import (ForgeError, MAX_JSON, atomic_write, digest, json_bytes, read_bytes,
                            read_json, relative_path, require, safe_path)

SKILL_NAME = re.compile(r"of-[a-z0-9]+(?:-[a-z0-9]+)*\Z")
FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")
RECEIPT_KIND = "osint-forge-standalone"
MAX_INSTALL_BYTES = 256 * 1024 * 1024


def prefix(client: str, scope: str) -> str:
    project = {"claude": ".claude/skills", "codex": ".agents/skills",
               "opencode": ".opencode/skills", "gemini": ".gemini/skills"}
    require(client in project and scope in ("project", "user"), "INVALID_INSTALL_TARGET")
    return ".config/opencode/skills" if client == "opencode" and scope == "user" else project[client]


def locations(base, client, scope):
    parent = safe_path(base / ".osint-forge-skills", exists=False)
    return parent / f"{client}-{scope}.json", parent / f"transaction-{client}-{scope}"


def selection(selected, available):
    require(selected is None or isinstance(selected, list) and bool(selected)
            and all(isinstance(name, str) for name in selected), "UNKNOWN_SKILL")
    chosen = sorted(set(available if selected is None else selected))
    require(bool(chosen) and set(chosen) <= set(available), "UNKNOWN_SKILL")
    return chosen


def owned_path(name, destination, skills):
    relative_path(name)
    require(name.startswith(destination + "/"), "INVALID_INSTALL_RECEIPT")
    parts = Path(name[len(destination) + 1:]).parts
    require(len(parts) >= 2 and parts[0] in skills, "INVALID_INSTALL_RECEIPT")
    member = "/".join(parts[1:])
    allowed = member in ("SKILL.md", "LICENSE", "NOTICE", "agents/openai.yaml", "scripts/forge.py")
    allowed = allowed or len(parts) == 3 and parts[1] == "references" and parts[2].endswith(".md")
    allowed = allowed or len(parts) == 4 and parts[1:3] == ("scripts", "forgekit") and parts[3].endswith(".py")
    allowed = allowed or len(parts) == 3 and parts[1] == "assets" and Path(parts[2]).suffix in (".svg", ".png", ".jpg", ".json", ".txt")
    require(allowed, "INVALID_INSTALL_RECEIPT")
    return parts[0]


def load_receipt(path, client, scope, destination, optional=False):
    safe_path(path, exists=False)
    if optional and not path.exists():
        return None, {}
    value = read_json(path)
    require(isinstance(value, dict) and type(value.get("schema_version")) is int
            and value["schema_version"] in (1, 2) and value.get("client") == client
            and value.get("scope") == scope, "INVALID_INSTALL_RECEIPT")
    skills = value.get("skills")
    require(isinstance(skills, list) and 0 < len(skills) <= 128
            and all(isinstance(name, str) and bool(SKILL_NAME.fullmatch(name)) for name in skills)
            and len(skills) == len(set(skills)), "INVALID_INSTALL_RECEIPT")
    if value["schema_version"] == 2:
        versions = value.get("skill_versions")
        require(value.get("kind") == RECEIPT_KIND and isinstance(versions, dict)
                and set(versions) == set(skills)
                and all(isinstance(version, str) and 0 < len(version) <= 100
                        for version in versions.values()), "INVALID_INSTALL_RECEIPT")
    rows = value.get("files")
    require(isinstance(rows, list) and 0 < len(rows) <= 20000, "INVALID_INSTALL_RECEIPT")
    files = {}
    for row in rows:
        require(isinstance(row, dict) and set(row) == {"path", "sha256"}
                and isinstance(row.get("path"), str), "INVALID_INSTALL_RECEIPT")
        name = row["path"]
        owned_path(name, destination, skills)
        require(name not in files and isinstance(row.get("sha256"), str)
                and bool(FINGERPRINT.fullmatch(row["sha256"])), "INVALID_INSTALL_RECEIPT")
        files[name] = row["sha256"]
    require(all(destination + "/" + skill + "/SKILL.md" in files for skill in skills),
            "INVALID_INSTALL_RECEIPT")
    return value, files


def receipt_bytes(client, scope, files, versions):
    data = json_bytes({"schema_version": 2, "kind": RECEIPT_KIND, "client": client,
                       "scope": scope, "skills": sorted(versions), "skill_versions": versions,
                       "files": [{"path": name, "sha256": fingerprint}
                                 for name, fingerprint in sorted(files.items())]})
    require(len(data) <= MAX_JSON, "INSTALL_RECEIPT_TOO_LARGE")
    return data


@contextmanager
def installation_lock(base, client, scope):
    prefix(client, scope)
    receipt, _ = locations(base, client, scope)
    safe_path(receipt.parent, exists=False).mkdir(mode=0o700, parents=True, exist_ok=True)
    path = safe_path(receipt.parent / f".{client}-{scope}.lock", exists=False)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    locked = False
    try:
        entry = os.fstat(descriptor)
        require(stat.S_ISREG(entry.st_mode) and entry.st_nlink == 1, "INVALID_INSTALL_LOCK")
        if os.name == "nt":
            import msvcrt
            if entry.st_size == 0:
                os.write(descriptor, b"0")
            os.lseek(descriptor, 0, os.SEEK_SET)
            try:
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise ForgeError("INSTALL_BUSY") from error
        else:
            import fcntl
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ForgeError("INSTALL_BUSY") from error
        locked = True
        yield
    finally:
        if locked:
            if os.name == "nt":
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def current_bytes(path):
    safe_path(path, exists=False)
    return read_bytes(path) if path.exists() else None


def write_target(path, data):
    if data is None:
        safe_path(path).unlink()
    else:
        safe_path(path.parent, exists=False).mkdir(parents=True, exist_ok=True, mode=0o700)
        atomic_write(path, data, replace=path.exists())


def clean_transaction(transaction):
    require(safe_path(transaction).is_dir(), "INVALID_INSTALL_TRANSACTION")
    for entry in transaction.iterdir():
        safe_path(entry)
        require(entry.is_file() and (entry.name == "manifest.json" or bool(re.fullmatch(
            r"[0-9]+\.(?:before|after)|\.forge-[A-Za-z0-9_-]{8}", entry.name))),
            "INSTALL_TRANSACTION_CONTENT_CHANGED")
    shutil.rmtree(safe_path(transaction))


def prune(base, names, destination):
    parents = set()
    for name in names:
        parents.update(parent for parent in (base / name).parents
                       if parent != base and parent.is_relative_to(base / destination))
    for parent in sorted(parents, key=lambda path: len(path.parts), reverse=True):
        if parent.exists() and not any(parent.iterdir()):
            safe_path(parent).rmdir()


def transaction_entries(base, transaction, manifest):
    require(isinstance(manifest, dict) and type(manifest.get("schema_version")) is int
            and manifest["schema_version"] == 1
            and isinstance(manifest.get("entries"), list)
            and 0 < len(manifest["entries"]) <= 20001, "INVALID_INSTALL_TRANSACTION")
    destination = prefix(manifest.get("client"), manifest.get("scope"))
    receipt, expected = locations(base, manifest["client"], manifest["scope"])
    require(transaction == expected and isinstance(manifest.get("skills"), list)
            and all(isinstance(skill, str) and SKILL_NAME.fullmatch(skill)
                    for skill in manifest["skills"]), "INVALID_INSTALL_TRANSACTION")
    entries, names, total = [], set(), 0
    for index, row in enumerate(manifest["entries"]):
        require(isinstance(row, dict) and set(row) == {"path", "before", "after"}
                and isinstance(row.get("path"), str), "INVALID_INSTALL_TRANSACTION")
        name = relative_path(row["path"])
        if name != receipt.relative_to(base).as_posix():
            owned_path(name, destination, manifest["skills"])
        require(name not in names, "INVALID_INSTALL_TRANSACTION")
        names.add(name)
        values = []
        for kind in ("before", "after"):
            fingerprint = row[kind]
            require(fingerprint is None or isinstance(fingerprint, str)
                    and bool(FINGERPRINT.fullmatch(fingerprint)), "INVALID_INSTALL_TRANSACTION")
            data = None if fingerprint is None else read_bytes(transaction / f"{index}.{kind}")
            require(data is None or digest(data) == fingerprint, "INSTALL_TRANSACTION_CHANGED")
            total += 0 if data is None else len(data)
            require(total <= 2 * MAX_INSTALL_BYTES + 2 * MAX_JSON, "INSTALL_TRANSACTION_TOO_LARGE")
            values.append(data)
        entries.append((name, *values))
    require(entries[-1][0] == receipt.relative_to(base).as_posix(), "INVALID_INSTALL_TRANSACTION")
    return entries


def rollback(base, transaction, manifest):
    entries = transaction_entries(base, transaction, manifest)
    for name, before, after in entries:
        require(current_bytes(base / name) in (before, after), "INSTALL_RECOVERY_CONFLICT")
    for name, before, after in reversed(entries):
        if current_bytes(base / name) != before:
            write_target(base / name, before)


def transact(base, client, scope, changes, receipt_data, skills):
    receipt, transaction = locations(base, client, scope)
    require(not transaction.exists(), "INSTALL_TRANSACTION_PENDING")
    before_receipt = current_bytes(receipt)
    entries = [(name, before, after) for name, (before, after) in sorted(changes.items()) if before != after]
    if not entries and before_receipt == receipt_data:
        return 0
    entries.append((receipt.relative_to(base).as_posix(), before_receipt, receipt_data))
    transaction.mkdir(mode=0o700)
    manifest = {"schema_version": 1, "client": client, "scope": scope,
                "skills": sorted(skills), "entries": []}
    try:
        for index, (name, before, after) in enumerate(entries):
            row = {"path": name}
            for kind, data in (("before", before), ("after", after)):
                row[kind] = None if data is None else digest(data)
                if data is not None:
                    atomic_write(transaction / f"{index}.{kind}", data)
            manifest["entries"].append(row)
        manifest_data = json_bytes(manifest)
        require(len(manifest_data) <= MAX_JSON, "INSTALL_TRANSACTION_TOO_LARGE")
        atomic_write(transaction / "manifest.json", manifest_data)
        for name, before, after in entries:
            require(current_bytes(base / name) == before, "INSTALLED_FILE_CHANGED")
            if before != after:
                write_target(base / name, after)
        require(all(current_bytes(base / name) == after for name, _, after in entries),
                "INSTALLED_FILE_CHANGED")
    except BaseException:
        if (transaction / "manifest.json").exists():
            try:
                rollback(base, transaction, manifest)
            except BaseException as error:
                raise ForgeError("INSTALL_RECOVERY_REQUIRED") from error
        clean_transaction(transaction)
        prune(base, [name for name, _, _ in entries[:-1]], prefix(client, scope))
        raise
    clean_transaction(transaction)
    return len(entries) - 1


def recover(target, client, scope, dry_run=False):
    base = safe_path(target)
    destination = prefix(client, scope)
    with nullcontext() if dry_run else installation_lock(base, client, scope):
        _, transaction = locations(base, client, scope)
        safe_path(transaction)
        manifest_path = transaction / "manifest.json"
        if not manifest_path.exists():
            if not dry_run:
                clean_transaction(transaction)
            return {"status": "dry_run" if dry_run else "recovered", "outcome": "discarded_unpublished_staging"}
        manifest = read_json(manifest_path)
        require(isinstance(manifest, dict) and manifest.get("client") == client and manifest.get("scope") == scope,
                "INVALID_INSTALL_TRANSACTION")
        entries = transaction_entries(base, transaction, manifest)
        for name, before, after in entries:
            require(current_bytes(base / name) in (before, after), "INSTALL_RECOVERY_CONFLICT")
        committed = all(current_bytes(base / name) == after for name, _, after in entries)
        if not dry_run:
            if not committed:
                rollback(base, transaction, manifest)
            clean_transaction(transaction)
            prune(base, [name for name, _, _ in entries[:-1]], destination)
        return {"status": "dry_run" if dry_run else "recovered",
                "outcome": "completed" if committed else "rolled_back", "file_count": len(entries) - 1}


def manage(target, client, scope, selected, dry_run, action):
    base = safe_path(target)
    require(base.is_dir(), "DIRECTORY_REQUIRED")
    destination = prefix(client, scope)
    with nullcontext() if dry_run else installation_lock(base, client, scope):
        receipt, transaction = locations(base, client, scope)
        require(not transaction.exists(), "INSTALL_TRANSACTION_PENDING")
        previous, owned = load_receipt(receipt, client, scope, destination, optional=action == "install")
        versions = {} if previous is None else dict(previous.get("skill_versions", {
            name: "legacy-unversioned" for name in previous["skills"]}))
        if action == "uninstall":
            chosen = selection(selected, versions)
            source = {}
            version = None
        else:
            if action == "update":
                chosen = selection(selected, versions)
                version, source = installation_files(chosen)
            else:
                version, source = installation_files(selected)
                chosen = sorted({name.split("/")[0] for name in source})
        wanted = {destination + "/" + name: data for name, data in source.items()}
        require(sum(len(data) for data in wanted.values()) <= MAX_INSTALL_BYTES, "INSTALLATION_TOO_LARGE")
        selected_old = {name: fingerprint for name, fingerprint in owned.items()
                        if owned_path(name, destination, versions) in chosen}
        before, total = {}, 0
        for name, fingerprint in selected_old.items():
            data = current_bytes(base / name)
            require(data is not None and digest(data) == fingerprint, "INSTALLED_FILE_MODIFIED")
            total += len(data)
            require(total <= MAX_INSTALL_BYTES, "INSTALLATION_TOO_LARGE")
            before[name] = data
        if action == "install":
            for skill in chosen:
                if skill not in versions:
                    require(not safe_path(base / destination / skill, exists=False).exists(), "SKILL_COLLISION")
                else:
                    actual = {name: digest(data) for name, data in wanted.items() if name.startswith(destination + "/" + skill + "/")}
                    prior = {name: fingerprint for name, fingerprint in selected_old.items() if name.startswith(destination + "/" + skill + "/")}
                    require(actual == prior, "INSTALL_UPDATE_REQUIRED")
        for name in wanted:
            owned_path(name, destination, chosen)
            if name not in selected_old:
                require(not safe_path(base / name, exists=False).exists(), "SKILL_COLLISION")
        final_files = {name: fingerprint for name, fingerprint in owned.items() if name not in selected_old}
        final_files.update({name: digest(data) for name, data in wanted.items()})
        for skill in chosen:
            if action == "uninstall":
                versions.pop(skill)
            else:
                versions[skill] = version
        changes = {name: (before.get(name), wanted.get(name)) for name in set(selected_old) | set(wanted)}
        changed = sum(old != new for old, new in changes.values())
        result = {"status": "dry_run" if dry_run else {"install": "installed", "update": "updated", "uninstall": "uninstalled"}[action],
                  "client": client, "scope": scope, "skills": chosen,
                  "installed_skills": sorted(versions), "file_count": len(selected_old) if action == "uninstall" else len(wanted),
                  "changed_files": 0 if dry_run else changed, "planned_changes": changed}
        if action == "uninstall":
            result["removed_files"] = len(selected_old)
        if not dry_run:
            data = receipt_bytes(client, scope, final_files, versions) if versions else None
            transact(base, client, scope, changes, data, set(versions) | set(chosen))
            prune(base, changes, destination)
        return result


def install(target, client, scope, selected=None, dry_run=False):
    return manage(target, client, scope, selected, dry_run, "install")


def update(target, client, scope, selected=None, dry_run=False):
    return manage(target, client, scope, selected, dry_run, "update")


def uninstall(target, client, scope, dry_run=False, selected=None):
    return manage(target, client, scope, selected, dry_run, "uninstall")


def main():
    parser = argparse.ArgumentParser(description="Offline standalone installation with versioned receipts and recoverable transactions.")
    parser.add_argument("action", choices=("install", "update", "uninstall", "recover"))
    parser.add_argument("--client", choices=("claude", "codex", "opencode", "gemini"), required=True)
    parser.add_argument("--target", required=True, help="Explicit existing project or user home directory")
    parser.add_argument("--scope", choices=("project", "user"), default="project")
    parser.add_argument("--skill", action="append", help="Select standalone skills for install, update or removal")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "recover":
            require(not args.skill, "RECOVERY_USES_TRANSACTION")
            result = recover(args.target, args.client, args.scope, args.dry_run)
        else:
            result = manage(args.target, args.client, args.scope, args.skill, args.dry_run, args.action)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ForgeError, OSError, ValueError, TypeError) as error:
        print(json.dumps({"status": "error", "code": str(error) if isinstance(error, ForgeError) else "INSTALL_IO_ERROR"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
