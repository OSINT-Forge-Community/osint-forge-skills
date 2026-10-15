from __future__ import annotations

import io
import json

from .exchange import source
from .safeio import ForgeError, MAX_RECORDS, require
from .timestamps import timestamp

EVENT_TYPES = ("model_text", "tool_request", "tool_result", "host_observation")


def agent_events(case, identifier, format_name):
    provenance, data = source(case, identifier)
    reject = lambda _: (_ for _ in ()).throw(ValueError())
    try:
        text = data.decode("utf-8-sig")
        if format_name == "json":
            payload = json.loads(text, parse_constant=reject)
            require(isinstance(payload, dict) and set(payload) == {"format", "events"}
                    and payload["format"] == "of-agent-events-v1", "UNSUPPORTED_AGENT_EXPORT")
            rows = payload["events"]
        else:
            require(format_name == "jsonl", "UNSUPPORTED_AGENT_EXPORT")
            rows = []
            for line in io.StringIO(text):
                require(len(rows) < MAX_RECORDS, "INVALID_AGENT_EVENTS")
                rows.append(json.loads(line, parse_constant=reject))
        require(isinstance(rows, list) and len(rows) <= MAX_RECORDS, "INVALID_AGENT_EVENTS")
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ForgeError("INVALID_AGENT_EXPORT") from exc
    events, gaps, requests = [], [], {}
    for index, row in enumerate(rows):
        require(isinstance(row, dict), "INVALID_AGENT_EVENT")
        require(format_name != "jsonl" or row.get("format") == "of-agent-events-v1", "UNSUPPORTED_AGENT_EXPORT")
        kind = row.get("event_type")
        require(isinstance(kind, str) and 0 < len(kind) <= 100, "INVALID_AGENT_EVENT")
        content = row.get("text", "")
        require(isinstance(content, str) and len(content) <= 4000 and "\x00" not in content, "INVALID_AGENT_EVENT_TEXT")
        call = row.get("call_id")
        require(call is None or isinstance(call, str) and 0 < len(call) <= 200, "INVALID_AGENT_CALL_ID")
        moment = row.get("timestamp")
        require(moment is None or isinstance(moment, str) and len(moment) <= 100, "INVALID_AGENT_TIME")
        normalized = timestamp(moment)
        event = {"evidence_id": identifier, "record_index": index, "event_type": kind,
                 "event": content, "original_timestamp": moment, **normalized,
                 "call_id": call, "effect_verified": False,
                 "interpretation": "unrecognized_record" if kind not in EVENT_TYPES else
                    {"model_text": "model_statement_not_evidence_of_effect", "tool_request": "requested_not_executed",
                     "tool_result": "reported_result_not_host_corroboration",
                     "host_observation": "supplied_host_observation_requires_provenance_review"}[kind]}
        if kind == "tool_request" and call:
            requests.setdefault(call, []).append(index)
        events.append(event)
        if kind not in EVENT_TYPES:
            gaps.append({"record_index": index, "code": "UNKNOWN_AGENT_EVENT_TYPE"})
        if kind in ("tool_request", "tool_result") and call is None:
            gaps.append({"record_index": index, "code": "MISSING_AGENT_CALL_ID"})
        ignored = set(row) - {"format", "event_type", "text", "timestamp", "call_id"}
        if ignored:
            gaps.append({"record_index": index, "code": "UNMAPPED_AGENT_FIELDS", "field_count": len(ignored)})
    for event in events:
        if event["event_type"] != "tool_result" or event["call_id"] is None:
            continue
        matches = requests.get(event["call_id"], [])
        if len(matches) == 1 and matches[0] < event["record_index"]:
            event["request_record_index"] = matches[0]
        else:
            gaps.append({"record_index": event["record_index"], "code": "AMBIGUOUS_OR_MISSING_TOOL_REQUEST"})
    return {"analysis_type": "agent_events", "export_format": "of-agent-events-v1", "input": provenance,
            "events": events, "event_count": len(events), "gaps": gaps, "network_calls": False,
            "limitations": ["Only an explicitly supplied normalized export is parsed; native client logs are not auto-detected.",
                            "A request, result or model narrative does not establish an effect on a host.",
                            "Host observations need separately reviewed provenance; shared timestamps do not prove causation.",
                            "Unknown event types and unmapped fields remain visible as gaps; originals are unchanged."]}
