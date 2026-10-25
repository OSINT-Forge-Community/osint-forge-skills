from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def serialized(value):
    return value.model_dump(by_alias=True, exclude_none=True)


async def exercise(helper, runtime_python, case=None):
    from jsonschema import Draft202012Validator
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    arguments = ["-I", str(helper), "mcp"]
    if case is not None:
        arguments.extend(["--case", str(case)])
    parameters = StdioServerParameters(command=runtime_python, args=arguments)
    with tempfile.TemporaryFile(mode="w+") as errors:
        async with stdio_client(parameters, errlog=errors) as (incoming, outgoing):
            async with ClientSession(incoming, outgoing, read_timeout_seconds=15) as session:
                initialized = serialized(await session.initialize())
                listed = serialized(await session.list_tools())["tools"]
                definitions = {row["name"]: row for row in listed}
                assert len(listed) == (7 if case is not None else 5)
                examples = {
                    "forge_plan": {"question": "Which synthetic observation supports the finding?", "kinds": ["documents"],
                        "available": ["local"], "authorized": ["local"], "max_steps": 5, "specialize": True},
                    "forge_sources": {"category": "domain", "applicable_to": "FR"},
                    "forge_pivots": {"kind": "document"},
                    "forge_queries": {"kind": "domain", "value": "example.org"},
                    "forge_dorks": {"phrase": "Synthetic harbor", "site": "example.org"},
                }
                if case is not None:
                    examples.update(forge_verify_case={}, forge_review_summary={})
                for name, inputs in examples.items():
                    result = serialized(await session.call_tool(name, inputs))
                    assert not result.get("isError", False)
                    schema = definitions[name]["outputSchema"]
                    Draft202012Validator.check_schema(schema)
                    Draft202012Validator(schema).validate(result["structuredContent"])
                invalid = serialized(await session.call_tool("forge_plan", {"question": "Synthetic", "kinds": ["documents"], "max_steps": 21}))
                assert invalid["isError"] is True
                assert invalid["structuredContent"]["field"] == "$.max_steps"
                Draft202012Validator(definitions["forge_plan"]["outputSchema"]).validate(invalid["structuredContent"])
                resources = serialized(await session.list_resources())["resources"]
                available = {row["uri"] for row in resources}
                assert "forge://contracts/case" in available
                method = next(uri for uri in sorted(available) if uri.startswith("forge://skills/"))
                for uri in ("forge://contracts/case", "forge://recipes/research", method):
                    result = serialized(await session.read_resource(uri))
                    assert result["contents"][0]["text"]
                rejected = False
                try:
                    await session.read_resource("file:///synthetic-private-path")
                except Exception:
                    rejected = True
                assert rejected
                await session.send_ping()
                if case is not None:
                    result = serialized(await session.call_tool("forge_plan", {"question": "Synthetic", "kinds": ["documents"], "use_case_summary": True}))
                    assert not result.get("isError", False)
                    assert "counts_by_kind" in result["structuredContent"]["case_review"]
        errors.seek(0)
        assert not errors.read()
    return {"protocol_version": initialized["protocolVersion"], "tool_count": len(listed), "resource_count": len(resources),
            "all_tools_called": True, "schemas_validated_by_jsonschema": True, "actionable_tool_error": True,
            "static_resources_read": True, "arbitrary_resource_rejected": True, "ping": "passed", "shutdown": "passed"}


def main():
    parser = argparse.ArgumentParser(description="Exercise the local server through an explicitly installed official MCP Python SDK; synthetic data only.")
    parser.add_argument("--helper", type=Path, default=Path(__file__).resolve().parents[1] / "scripts/forge.py")
    parser.add_argument("--runtime-python", default=sys.executable)
    args = parser.parse_args()
    try:
        sdk_version = version("mcp")
        helper = args.helper.resolve(strict=True)
        with tempfile.TemporaryDirectory(prefix="forge-mcp-sdk-") as temporary:
            case = Path(temporary) / "case"
            result = subprocess.run([args.runtime_python, "-I", str(helper), "init", "--case", str(case),
                "--title", "Synthetic MCP compatibility", "--scope", "Original synthetic fixture only"],
                capture_output=True, timeout=15)
            assert result.returncode == 0
            checks = asyncio.run(exercise(helper, args.runtime_python))
            case_checks = asyncio.run(exercise(helper, args.runtime_python, case))
        output = {"status": "passed", "scope": "official_sdk_stdio_synthetic", "sdk_package": "mcp", "sdk_version": sdk_version,
            "python_version": sys.version.split()[0], "observed_at": datetime.now(timezone.utc).isoformat(),
            "default": checks, "startup_case": case_checks, "real_host_trial": "not_run", "model_trial": "not_run",
            "provider_configuration_changed": False, "global_configuration_changed": False}
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except Exception:
        print(json.dumps({"status": "failed", "code": "SDK_TRIAL_FAILED",
            "next_check": "Install the selected official MCP SDK in an isolated development environment and inspect the synthetic trial locally"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
