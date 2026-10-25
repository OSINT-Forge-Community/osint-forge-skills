from __future__ import annotations

import hashlib
from contextlib import contextmanager
from contextvars import ContextVar
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import time

MAX_FILE = 64 * 1024 * 1024
MAX_JSON = 4 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024
MAX_RECORDS = 5000
_BUDGET = ContextVar("forge_budget", default=None)
_READS = ContextVar("forge_reads", default=None)


class ForgeError(Exception):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ForgeError(code)


@contextmanager
def operation_budget(seconds=30, max_bytes=512 * 1024 * 1024, cancel=None):
    require(isinstance(seconds, (int, float)) and 0 < seconds <= 3600
            and type(max_bytes) is int and 0 < max_bytes <= 4 * 1024**3, "INVALID_OPERATION_BUDGET")
    token = _BUDGET.set({"deadline": time.monotonic() + seconds, "remaining": max_bytes, "cancel": cancel})
    try:
        checkpoint()
        yield
    finally:
        _BUDGET.reset(token)


def checkpoint(byte_count=0):
    budget = _BUDGET.get()
    if budget is None:
        return
    cancel = budget["cancel"]
    require(cancel is None or not (cancel.is_set() if hasattr(cancel, "is_set") else cancel()),
            "OPERATION_CANCELLED")
    budget["remaining"] -= byte_count
    require(budget["remaining"] >= 0 and time.monotonic() <= budget["deadline"],
            "OPERATION_BUDGET_EXCEEDED")


def file_signature(entry):
    return (entry.st_dev, entry.st_ino, entry.st_size, entry.st_mtime_ns, entry.st_ctime_ns)


@contextmanager
def read_scope(root, maximum=16 * 1024 * 1024):
    require(type(maximum) is int and 0 <= maximum <= MAX_TOTAL, "INVALID_READ_SCOPE")
    previous = _READS.get()
    if previous is not None and previous["root"] == root:
        yield previous
        return
    scope = {"root": root, "bytes": {}, "signatures": {}, "digests": {}, "size": 0, "maximum": maximum}
    token = _READS.set(scope)
    try:
        yield scope
        for path, signature in scope["signatures"].items():
            checkpoint()
            require(file_signature(safe_path(path).lstat()) == signature, "CASE_CHANGED_DURING_READ")
        validation = _READS.set(None)
        try:
            for path, expected in scope["digests"].items():
                checkpoint()
                selected = safe_path(path)
                actual, signature = _read_file(selected, selected.lstat(), scope["signatures"][path][2], False)
                require(actual == expected and signature == scope["signatures"][path],
                        "CASE_CHANGED_DURING_READ")
        finally:
            _READS.reset(validation)
    finally:
        _READS.reset(token)


def safe_path(value: str | Path, *, exists: bool = True) -> Path:
    path = Path(os.path.abspath(os.fspath(value)))
    parts = [part.lower() for part in path.parts]
    require(not any(a == "envs" and b == "production"
                    for a, b in zip(parts, parts[1:])), "PROHIBITED_PATH")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            entry = current.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(entry.st_mode), "SYMLINK_REJECTED")
    if exists:
        require(path.exists(), "PATH_MISSING")
    return path


def relative_path(value: str) -> str:
    require(isinstance(value, str) and bool(value), "INVALID_RELATIVE_PATH")
    require("\\" not in value and ":" not in value and "\x00" not in value,
            "INVALID_RELATIVE_PATH")
    parts = PurePosixPath(value)
    require(not parts.is_absolute() and ".." not in parts.parts,
            "INVALID_RELATIVE_PATH")
    require(parts.as_posix() == value and value != ".", "INVALID_RELATIVE_PATH")
    return value


def read_bytes(value: str | Path, limit: int = MAX_FILE) -> bytes:
    checkpoint()
    path = safe_path(value)
    entry = path.lstat()
    require(stat.S_ISREG(entry.st_mode), "REGULAR_FILE_REQUIRED")
    scope = _READS.get()
    scope = scope if scope is not None and path.is_relative_to(scope["root"]) else None
    if scope is not None:
        signature = file_signature(entry)
        previous = scope["signatures"].get(path)
        require(previous is None or previous == signature, "CASE_CHANGED_DURING_READ")
        cached = scope["bytes"].get(path)
        if cached is not None:
            require(len(cached) <= limit, "FILE_TOO_LARGE")
            return cached
    data, signature = _read_file(path, entry, limit, True)
    if scope is not None:
        require(len(scope["signatures"]) < MAX_RECORDS * 4 or path in scope["signatures"], "TOO_MANY_READ_FILES")
        fingerprint = digest(data)
        require(path not in scope["digests"] or scope["digests"][path] == fingerprint,
                "CASE_CHANGED_DURING_READ")
        scope["signatures"].setdefault(path, signature)
        scope["digests"].setdefault(path, fingerprint)
        if len(data) <= scope["maximum"] - scope["size"]:
            scope["bytes"][path] = data
            scope["size"] += len(data)
    return data


def _read_file(path, entry, limit, retain):
    require(stat.S_ISREG(entry.st_mode), "REGULAR_FILE_REQUIRED")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                         | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(descriptor, "rb") as handle:
        before = os.fstat(handle.fileno())
        require(stat.S_ISREG(before.st_mode), "REGULAR_FILE_REQUIRED")
        require((entry.st_dev, entry.st_ino) == (before.st_dev, before.st_ino),
                "SOURCE_CHANGED")
        require(before.st_size <= limit, "FILE_TOO_LARGE")
        chunks, fingerprint, count = [], hashlib.sha256(), 0
        read_limit = min(limit, before.st_size) + 1
        while count < read_limit:
            chunk = handle.read(min(65536, read_limit - count))
            if not chunk:
                break
            if retain:
                chunks.append(chunk)
            else:
                fingerprint.update(chunk)
            count += len(chunk)
            checkpoint(len(chunk))
        after = os.fstat(handle.fileno())
        require(file_signature(before) == file_signature(after), "SOURCE_CHANGED")
        require(count <= limit and count == before.st_size, "SOURCE_CHANGED")
        final_entry = path.lstat()
        require(file_signature(entry) == file_signature(final_entry), "SOURCE_CHANGED")
    return b"".join(chunks) if retain else fingerprint.hexdigest(), file_signature(final_entry)


def digest(data: bytes) -> str:
    checkpoint()
    result = hashlib.sha256(data).hexdigest()
    checkpoint()
    return result


def atomic_write(value: str | Path, data: bytes, *, replace: bool = False) -> None:
    path = safe_path(value, exists=False)
    parent = safe_path(path.parent)
    require(parent.is_dir(), "DIRECTORY_REQUIRED")
    require(replace or not path.exists(), "OUTPUT_EXISTS")
    if path.exists():
        require(path.is_file() and path.stat().st_nlink == 1,
                "UNSAFE_OUTPUT_FILE")
    descriptor, temporary = tempfile.mkstemp(prefix=".forge-", dir=parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        safe_path(path, exists=False)
        if replace:
            os.replace(temporary, path)
        else:
            try:
                os.link(temporary, path, follow_symlinks=False)
            except FileExistsError as exc:
                raise ForgeError("OUTPUT_EXISTS") from exc
            except (NotImplementedError, OSError):
                out = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                              | getattr(os, "O_NOFOLLOW", 0)
                              | getattr(os, "O_BINARY", 0), 0o600)
                try:
                    with os.fdopen(out, "wb") as handle:
                        handle.write(data)
                        handle.flush()
                        os.fsync(handle.fileno())
                except BaseException:
                    path.unlink(missing_ok=True)
                    raise
    finally:
        Path(temporary).unlink(missing_ok=True)


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def read_json(path: str | Path) -> object:
    try:
        return json.loads(read_bytes(path, MAX_JSON),
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ForgeError("INVALID_JSON") from exc


def read_jsonl(path: str | Path) -> list[dict]:
    data = read_bytes(path, MAX_JSON)
    try:
        records = []
        for line in io.BytesIO(data):
            if not line.strip():
                continue
            require(len(records) < MAX_RECORDS, "TOO_MANY_RECORDS")
            records.append(json.loads(line, parse_constant=lambda _: (_ for _ in ()).throw(ValueError())))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ForgeError("INVALID_JSONL") from exc
    require(len(records) <= MAX_RECORDS, "TOO_MANY_RECORDS")
    require(all(isinstance(row, dict) for row in records), "INVALID_RECORD")
    return records


def jsonl_bytes(rows: list[dict]) -> bytes:
    require(len(rows) <= MAX_RECORDS, "TOO_MANY_RECORDS")
    data = b"".join((json.dumps(row, ensure_ascii=True, sort_keys=True,
                               allow_nan=False) + "\n").encode() for row in rows)
    require(len(data) <= MAX_JSON, "RECORDS_TOO_LARGE")
    return data


def visible(value: object, limit: int = 4000) -> str:
    text = str(value)[:limit]
    return "".join(c if c.isprintable() or c in "\n\t"
                   else "\\u%04x" % ord(c) for c in text)


def markdown(value: object, limit: int = 4000) -> str:
    text = visible(value, limit).replace("\n", " ").replace("\t", " ")
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"([\\`*{}_\[\]()#!|])", r"\\\1", text)


def zip_directory_guard(data: bytes, maximum: int) -> None:
    location = data.rfind(b"PK\x05\x06", max(0, len(data) - 65557))
    require(location >= 0 and len(data) - location >= 22, "INVALID_ZIP")
    import struct
    _, disk, directory_disk, on_disk, total, size, offset, comment = struct.unpack(
        "<4sHHHHIIH", data[location:location + 22])
    require(disk == directory_disk == 0 and on_disk == total, "UNSUPPORTED_MULTI_DISK_ZIP")
    require(total != 65535 and size != 4294967295 and offset != 4294967295,
            "UNSUPPORTED_ZIP64")
    require(total <= maximum, "ARCHIVE_TOO_MANY_ENTRIES")
    require(size <= MAX_JSON and offset + size <= location
            and location + 22 + comment == len(data), "INVALID_ZIP_DIRECTORY")
