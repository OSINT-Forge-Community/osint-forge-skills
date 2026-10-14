#!/usr/bin/env python3
from dataclasses import replace
import json
from benchflow.agents.registry import AGENTS, AGENT_INSTALLERS, AGENT_LAUNCH

old = AGENTS["codex-acp"]
assert "@agentclientprotocol/codex-acp@0.0.45" in old.install_cmd
install = old.install_cmd.replace("@agentclientprotocol/codex-acp@0.0.45", "@agentclientprotocol/codex-acp@2.2.2")
install += (
    " && /opt/benchflow/node/bin/npm install -g --prefix /opt/benchflow/codex @openai/codex@0.162.1"
    " && PATH=/opt/benchflow/node/bin:$PATH /opt/benchflow/codex/bin/codex --version"
    " && /opt/benchflow/bin/codex-acp --version"
    " && chmod -R a+rX /opt/benchflow/codex"
)
AGENTS["codex-acp"] = replace(
    old, install_cmd=install,
    launch_cmd="export PATH=/opt/benchflow/node/bin:$PATH; export CODEX_PATH=/opt/benchflow/codex/bin/codex; exec " + old.launch_cmd,
)
AGENT_INSTALLERS["codex-acp"] = AGENTS["codex-acp"].install_cmd
AGENT_LAUNCH["codex-acp"] = AGENTS["codex-acp"].launch_cmd
assert "codex-acp@2.2.2" in AGENT_INSTALLERS["codex-acp"]
assert "CODEX_PATH=/opt/benchflow/codex/bin/codex" in AGENT_LAUNCH["codex-acp"]

from benchflow.acp import runtime

original_select = runtime._select_acp_model_id
original_configure = runtime._configure_acp_session

def select_model(model, agent, session):
    if agent == "codex-acp" and "model" in runtime._session_config_option_ids(session):
        return model
    return original_select(model, agent, session)

async def configure(client, session, **kwargs):
    await original_configure(client, session, **kwargs)
    if kwargs["agent"] != "codex-acp":
        return
    requested = json.loads(kwargs["agent_env"]["CODEX_CONFIG"])
    options = {x["id"]: x for x in session.config_options}
    effort = next((x for x in options.values() if x.get("category") == "thought_level" or x["id"] in {"reasoning_effort", "reasoning-effort", "thought_level"}), None)
    if effort is None:
        raise RuntimeError("Current adapter did not expose a reasoning option: " + ",".join(options))
    await runtime._set_acp_config_option(client, session, agent="codex-acp", config_id=effort["id"], value=requested["model_reasoning_effort"], label="reasoning effort")
    options = {x["id"]: x for x in session.config_options}
    observed = {"model": options["model"].get("currentValue"), "reasoning_effort": options[effort["id"]].get("currentValue")}
    if observed != {"model": requested["model"], "reasoning_effort": requested["model_reasoning_effort"]}:
        raise RuntimeError("Adapter configuration mismatch: " + json.dumps(observed))
    print("SKILLSBENCH_OBSERVED_CONFIGURATION " + json.dumps(observed), flush=True)

runtime._select_acp_model_id = select_model
runtime._configure_acp_session = configure

from benchflow.cli.main import app
app()
