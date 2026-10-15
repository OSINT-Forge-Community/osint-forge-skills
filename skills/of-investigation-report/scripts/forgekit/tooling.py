from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import tempfile
import threading
import time

from .analysis import save_analysis
from .casefiles import evidence_bytes, load_case, utc_now, verify
from .safeio import ForgeError, MAX_JSON, digest, json_bytes, read_bytes, read_json, require, safe_path
from .review import checked_analysis

TOOLS = {
    "exiftool": ("Image and PDF metadata", ["-config", "", "-ver"]),
    "ffprobe": ("Media container and stream metadata", ["-version"]),
    "pdftotext": ("Text from a selected PDF page range", ["-v"]),
    "tesseract": ("OCR from one PNG or JPEG image", ["--version"]),
}
OUTPUT_LIMIT = 512 * 1024
ERROR_LIMIT = 16 * 1024
TIMEOUT = 30


def inventory() -> dict:
    search = os.pathsep.join(part for part in os.get_exec_path()
                             if part and Path(part).is_absolute()
                             and Path(part).resolve() != Path.cwd().resolve())
    rows = []
    for name, (purpose, _) in TOOLS.items():
        located = shutil.which(name, path=search)
        rows.append({"tool": name, "purpose": purpose,
                     "executable": str(Path(located).resolve()) if located else None,
                     "status": "found_unverified" if located else "not_found"})
    return {"tools": rows, "executed": False, "installed": False,
            "note": "Discovery is not approval, version validation or a successful tool trial."}


def bounded_process(argv: list[str], cwd: Path, *, stdin=None,
                    timeout: float = TIMEOUT, output_limit: int = OUTPUT_LIMIT) -> tuple[int, bytes, bytes]:
    environment = {"PATH": os.defpath, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                   "HOME": str(cwd), "TMPDIR": str(cwd), "TEMP": str(cwd),
                   "TMP": str(cwd), "OMP_THREAD_LIMIT": "1"}
    for name in ("SYSTEMROOT", "WINDIR"):
        if name in os.environ:
            environment[name] = os.environ[name]
    buffers = [bytearray(), bytearray()]
    overflow = threading.Event()
    process = subprocess.Popen(argv, cwd=cwd, env=environment, shell=False,
                               stdin=subprocess.DEVNULL if stdin is None else stdin,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               bufsize=0, start_new_session=os.name == "posix")

    def consume(stream, target, limit):
        try:
            while chunk := stream.read(8192):
                remaining = limit - len(target)
                target.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    overflow.set()
                    break
        except OSError:
            overflow.set()

    readers = [threading.Thread(target=consume, args=(stream, buffers[index], limit), daemon=True)
               for index, (stream, limit) in enumerate(
                   ((process.stdout, output_limit), (process.stderr, ERROR_LIMIT)))]
    for reader in readers:
        reader.start()
    deadline = time.monotonic() + timeout
    try:
        while process.poll() is None or any(reader.is_alive() for reader in readers):
            require(not overflow.is_set(), "TOOL_OUTPUT_TOO_LARGE")
            require(time.monotonic() < deadline, "TOOL_TIMEOUT")
            time.sleep(0.01)
        require(not overflow.is_set(), "TOOL_OUTPUT_TOO_LARGE")
        return process.returncode, bytes(buffers[0]), bytes(buffers[1])
    finally:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        elif process.poll() is None:
            process.kill()
        process.wait()
        for reader in readers:
            reader.join(timeout=1)
        process.stdout.close()
        process.stderr.close()


def input_kind(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"%PDF-"):
        return "pdf"
    if data.startswith(b"RIFF") and data[8:12] == b"WAVE":
        return "wav"
    if data.startswith(b"RIFF") and data[8:12] == b"AVI ":
        return "avi"
    if data[4:8] == b"ftyp":
        return "mov"
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return "matroska"
    raise ForgeError("TOOL_INPUT_UNSUPPORTED")


def arguments(tool: str, kind: str, *, first_page: int, last_page: int, language: str) -> list[str]:
    require(tool in TOOLS, "UNKNOWN_TOOL")
    if tool == "exiftool":
        require(kind in ("png", "jpeg", "pdf"), "TOOL_INPUT_UNSUPPORTED")
        return ["-config", "", "-json", "-G1", "-a", "-n", f"input.{kind}"]
    if tool == "pdftotext":
        require(kind == "pdf", "TOOL_INPUT_UNSUPPORTED")
        require(1 <= first_page <= last_page and last_page - first_page < 20
                and last_page <= 100000, "INVALID_PAGE_RANGE")
        return ["-f", str(first_page), "-l", str(last_page), "-layout", "-enc", "UTF-8",
                "input.pdf", "-"]
    if tool == "tesseract":
        require(kind in ("png", "jpeg"), "TOOL_INPUT_UNSUPPORTED")
        require(bool(re.fullmatch(r"[a-z]{3}(?:\+[a-z]{3}){0,2}", language)), "INVALID_OCR_LANGUAGE")
        return [f"input.{kind}", "stdout", "-l", language, "--psm", "3"]
    require(kind in ("wav", "avi", "mov", "matroska"), "TOOL_INPUT_UNSUPPORTED")
    return ["-v", "error", "-protocol_whitelist", "pipe", "-format_whitelist", kind,
            "-f", kind, "-probesize", "5000000", "-analyzeduration", "5000000",
            "-show_format", "-show_streams", "-of", "json", "-i", "pipe:0"]


def parse_output(tool: str, stdout: bytes):
    if tool not in ("exiftool", "ffprobe"):
        return stdout.decode("utf-8")
    try:
        value = json.loads(stdout, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ForgeError("INVALID_TOOL_OUTPUT") from exc
    if tool == "exiftool":
        require(isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict),
                "INVALID_TOOL_OUTPUT")
        require(not any(key.split(":")[-1] == "Error" for key in value[0]), "TOOL_REPORTED_ERROR")
    else:
        require(isinstance(value, dict) and isinstance(value.get("streams"), list)
                and isinstance(value.get("format"), dict), "INVALID_TOOL_OUTPUT")
        require("error" not in value, "TOOL_REPORTED_ERROR")
    return value


def run_tool(case: str | Path, identifier: str, tool: str, executable: str,
             output: str | Path, *, first_page: int = 1, last_page: int = 1,
             language: str = "eng", reuse: str | None = None) -> dict:
    require(tool in TOOLS, "UNKNOWN_TOOL")
    require(Path(executable).is_absolute(), "ABSOLUTE_EXECUTABLE_REQUIRED")
    binary = safe_path(executable)
    require(stat.S_ISREG(binary.stat().st_mode) and os.access(binary, os.X_OK)
            and binary.suffix.lower() not in (".bat", ".cmd"), "INVALID_TOOL_EXECUTABLE")
    root, _, _, _ = load_case(case)
    require(not binary.is_relative_to(root), "TOOL_EXECUTABLE_INSIDE_CASE")
    destination = safe_path(output, exists=False)
    require(destination.is_relative_to(root / "analysis"), "ANALYSIS_OUTPUT_REQUIRED")
    require(not destination.exists(), "OUTPUT_EXISTS")
    require(destination.parent.is_dir(), "DIRECTORY_REQUIRED")
    row, data = evidence_bytes(root, identifier)
    kind = input_kind(data)
    options = arguments(tool, kind, first_page=first_page, last_page=last_page, language=language)
    binary_digest = digest(read_bytes(binary))
    started = utc_now()
    with tempfile.TemporaryDirectory(prefix="forge-tool-") as temporary:
        work = Path(temporary)
        copied = work / f"input.{kind}"
        copied.write_bytes(data)
        copied.chmod(0o400)
        try:
            code, version_out, version_error = bounded_process(
                [str(binary), *TOOLS[tool][1]], work, timeout=5, output_limit=ERROR_LIMIT)
            require(code == 0, "TOOL_VERSION_FAILED")
            version = (version_out + version_error).decode("utf-8", errors="replace").strip()
            require(bool(version), "TOOL_VERSION_FAILED")
            identity = {"evidence_sha256": row["sha256"], "executable_sha256": binary_digest,
                        "tool": tool, "version_output": version, "arguments": options}
            if reuse is not None:
                _, _, evidence, _ = load_case(root)
                previous, previous_digest = checked_analysis(root, reuse, evidence, evidence_id=identifier)
                require(previous.get("reuse_identity") == identity
                        and previous.get("analysis_type") == "external_tool"
                        and isinstance(previous.get("stdout"), str)
                        and digest(previous["stdout"].encode()) == previous.get("stdout_sha256"),
                        "REUSE_IDENTITY_MISMATCH")
                require(parse_output(tool, previous["stdout"].encode()) == previous.get("result"),
                        "REUSE_OUTPUT_MISMATCH")
                result = {**previous, "execution": "reused_not_independent_reproduction",
                          "reused_at": utc_now(), "reused_from": {"path": reuse, "sha256": previous_digest}}
                require(digest(read_bytes(binary)) == binary_digest, "TOOL_EXECUTABLE_CHANGED")
                return {**save_analysis(root, destination, result), "tool": tool,
                        "evidence_id": identifier, "execution": result["execution"]}
            with copied.open("rb") as source:
                code, stdout, stderr = bounded_process([str(binary), *options], work,
                                                      stdin=source if tool == "ffprobe" else None)
            require(code == 0, "TOOL_FAILED")
            require(digest(read_bytes(copied)) == row["sha256"], "TOOL_CHANGED_COPY")
            parsed = parse_output(tool, stdout)
            require(digest(read_bytes(binary)) == binary_digest, "TOOL_EXECUTABLE_CHANGED")
        finally:
            verify(root)
    result = {"analysis_type": "external_tool", "input": {"evidence_id": identifier,
              "sha256": row["sha256"]}, "tool": {"name": tool, "executable": str(binary),
              "version_output": version, "arguments": options, "returncode": code},
              "started_at": started, "finished_at": utc_now(),
              "stdout_sha256": digest(stdout), "stderr_sha256": digest(stderr),
              "stdout": stdout.decode("utf-8"),
              "reuse_identity": identity, "execution": "executed",
              "stderr": stderr.decode("utf-8", errors="replace"), "result": parsed,
              "coverage": {"first_page": first_page, "last_page": last_page}
                  if tool == "pdftotext" else {"mode": "single_selected_file"},
              "limits": {"seconds": TIMEOUT, "stdout_bytes": OUTPUT_LIMIT,
                         "stderr_bytes": ERROR_LIMIT},
              "limitations": ["External executable runs with host permissions; this is not a sandbox.",
                              "Tool output is untrusted data, not instructions or authenticity proof.",
                              "Temporary-copy filesystem times are not original capture times.",
                              "Successful execution does not prove complete or accurate extraction."]}
    return {**save_analysis(root, destination, result), "tool": tool, "evidence_id": identifier}
