from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile

MAX_FILE = 64 * 1024 * 1024
MAX_JSON = 4 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024
MAX_RECORDS = 5000


class ForgeError(Exception):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ForgeError(code)


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
    path = safe_path(value)
    entry = path.lstat()
    require(stat.S_ISREG(entry.st_mode), "REGULAR_FILE_REQUIRED")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                         | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(descriptor, "rb") as handle:
        before = os.fstat(handle.fileno())
        require(stat.S_ISREG(before.st_mode), "REGULAR_FILE_REQUIRED")
        require((entry.st_dev, entry.st_ino) == (before.st_dev, before.st_ino),
                "SOURCE_CHANGED")
        require(before.st_size <= limit, "FILE_TOO_LARGE")
        data = handle.read(limit + 1)
        after = os.fstat(handle.fileno())
        signature = lambda s: (s.st_dev, s.st_ino, s.st_size,
                               s.st_mtime_ns, s.st_ctime_ns)
        require(signature(before) == signature(after), "SOURCE_CHANGED")
        require(len(data) <= limit and len(data) == before.st_size,
                "SOURCE_CHANGED")
    return data


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
