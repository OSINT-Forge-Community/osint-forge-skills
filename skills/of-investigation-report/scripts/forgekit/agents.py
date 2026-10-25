from __future__ import annotations

import io
import json

from .exchange import source
from .safeio import ForgeError, MAX_RECORDS, require
from .timestamps import timestamp

EVENT_TYPES = ("model_text", "tool_request", "tool_result", "host_observation")
CODEX_PROFILE = "codex-exec-jsonl-2026-10-25"
CODEX_REFERENCE = "https://learn.chatgpt.com/docs/non-interactive-mode#make-output-machine-readable"


def export_rows(data, format_name):
    reject = lambda _: (_ for _ in ()).throw(ValueError())
    try:
        text = data.decode("utf-8-sig")
        if format_name == "json":
            payload = json.loads(text, parse_constant=reject)
            require(isinstance(payload, dict) and set(payload) == {"format", "events"}
                    and payload["format"] == "of-agent-events-v1", "UNSUPPORTED_AGENT_EXPORT")
            rows = payload["events"]
        else:
            require(format_name in ("jsonl", "codex-exec-jsonl"), "UNSUPPORTED_AGENT_EXPORT")
            rows = []
            for line in io.StringIO(text):
                require(len(rows) < MAX_RECORDS, "INVALID_AGENT_EVENTS")
                rows.append(json.loads(line, parse_constant=reject))
        require(isinstance(rows, list) and len(rows) <= MAX_RECORDS, "INVALID_AGENT_EVENTS")
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ForgeError("INVALID_AGENT_EXPORT") from exc
    return rows


def codex_rows(rows):
    converted, gaps, omitted = [], [], 0
    boundaries = {"thread.started", "turn.started", "turn.completed"}
    tools = {"command_execution", "mcp_tool_call", "web_search", "file_change"}
    for index, row in enumerate(rows):
        require(isinstance(row, dict), "INVALID_AGENT_EVENT")
        native_type = row.get("type")
        require(isinstance(native_type, str) and 0 < len(native_type) <= 100, "INVALID_AGENT_EVENT")
        if native_type in boundaries:
            omitted += 1
            gaps.append({"record_index": index, "code": "CODEX_METADATA_RECORD_NOT_CONVERTED"})
            continue
        item = row.get("item")
        item_kind = item.get("type") if isinstance(item, dict) else None
        require(item_kind is None or isinstance(item_kind, str) and 0 < len(item_kind) <= 100,
                "INVALID_AGENT_EVENT")
        item_id = item.get("id") if isinstance(item, dict) else None
        status = item.get("status") if isinstance(item, dict) else None
        require(item_id is None or isinstance(item_id, str) and 0 < len(item_id) <= 200, "INVALID_AGENT_CALL_ID")
        require(status is None or isinstance(status, str) and len(status) <= 100, "INVALID_AGENT_EVENT")
        content, call, kind = "", None, "unknown_native_event"
        item_used = set()
        if native_type in ("item.started", "item.completed", "item.updated") and isinstance(item, dict):
            if item_kind in ("agent_message", "reasoning"):
                kind = "model_text"
                content = item.get("text", "")
                item_used = {"type", "text", "id"}
            elif item_kind in tools and native_type != "item.updated":
                kind = "tool_request" if native_type == "item.started" else "tool_result"
                call = item.get("id")
                item_used = {"type", "id", "status"}
                if item_kind == "command_execution":
                    field = "command" if kind == "tool_request" else "aggregated_output"
                    content = item.get(field, "")
                    item_used.add(field)
                    if field not in item:
                        gaps.append({"record_index": index, "code": "CODEX_OPERATION_PAYLOAD_UNAVAILABLE"})
                elif item_kind == "mcp_tool_call":
                    fields = ("server", "tool", "arguments") if kind == "tool_request" else ("result", "error")
                    content = json.dumps({key: item[key] for key in fields if key in item}, ensure_ascii=False, sort_keys=True)
                    item_used.update(fields)
                elif item_kind == "web_search":
                    content = item.get("query", "")
                    item_used.add("query")
                else:
                    content = json.dumps(item.get("changes", []), ensure_ascii=False, sort_keys=True)
                    item_used.add("changes")
            else:
                gaps.append({"record_index": index, "code": "UNKNOWN_CODEX_ITEM_TYPE"})
        else:
            gaps.append({"record_index": index, "code": "UNKNOWN_CODEX_EVENT_TYPE"})
        require(isinstance(content, str) and "\x00" not in content, "INVALID_AGENT_EVENT_TEXT")
        if len(content) > 4000:
            gaps.append({"record_index": index, "code": "CODEX_EVENT_TEXT_CLIPPED", "original_characters": len(content)})
            content = content[:4000]
        ignored = len(set(row) - {"type", "timestamp", "item"})
        if isinstance(item, dict):
            ignored += len(set(item) - item_used)
        elif "item" in row:
            ignored += 1
        if ignored:
            gaps.append({"record_index": index, "code": "UNMAPPED_AGENT_FIELDS", "field_count": ignored})
        converted.append((index, {"event_type": kind, "text": content, "timestamp": row.get("timestamp"),
                                  "call_id": call}, {"native_event_type": native_type, "native_item_type": item_kind,
                                                     "native_item_id": item_id, "native_status": status}))
    return converted, gaps, omitted


def agent_events(case, identifier, format_name, exporter_version=None):
    provenance, data = source(case, identifier)
    rows = export_rows(data, format_name)
    require(exporter_version is None or isinstance(exporter_version, str)
            and 0 < len(exporter_version) <= 100 and "\x00" not in exporter_version, "INVALID_AGENT_EXPORTER_VERSION")
    native = format_name == "codex-exec-jsonl"
    if native:
        selected, gaps, omitted = codex_rows(rows)
    else:
        selected, gaps, omitted = [(index, row, {}) for index, row in enumerate(rows)], [], 0
    events, requests, results = [], {}, {}
    for index, row, native_context in selected:
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
        if native:
            event.update(source_line=index + 1, **native_context)
        if kind == "tool_request" and call:
            requests.setdefault(call, []).append(index)
        if kind == "tool_result" and call:
            results.setdefault(call, []).append(index)
        events.append(event)
        if kind not in EVENT_TYPES:
            gaps.append({"record_index": index, "code": "UNKNOWN_AGENT_EVENT_TYPE"})
        if kind in ("tool_request", "tool_result") and call is None:
            gaps.append({"record_index": index, "code": "MISSING_AGENT_CALL_ID"})
        ignored = set(row) - {"format", "event_type", "text", "timestamp", "call_id"}
        if ignored:
            gaps.append({"record_index": index, "code": "UNMAPPED_AGENT_FIELDS", "field_count": len(ignored)})
    for call, indices in requests.items():
        if len(indices) > 1:
            gaps.append({"record_index": indices[1], "code": "DUPLICATE_AGENT_CALL_ID", "request_count": len(indices)})
        if call not in results:
            for index in indices:
                gaps.append({"record_index": index, "code": "TOOL_REQUEST_WITHOUT_RESULT"})
    for indices in results.values():
        if len(indices) > 1:
            gaps.append({"record_index": indices[1], "code": "MULTIPLE_TOOL_RESULTS", "result_count": len(indices)})
    for event in events:
        if event["event_type"] != "tool_result" or event["call_id"] is None:
            continue
        matches = requests.get(event["call_id"], [])
        if len(matches) == 1 and matches[0] < event["record_index"] and len(results[event["call_id"]]) == 1:
            event["request_record_index"] = matches[0]
        else:
            gaps.append({"record_index": event["record_index"], "code": "AMBIGUOUS_OR_MISSING_TOOL_REQUEST"})
    return {"analysis_type": "agent_events", "export_format": "codex-exec-jsonl" if native else "of-agent-events-v1", "input": provenance,
            "exporter": {"name": "Codex CLI" if native else "operator_supplied", "reported_version": exporter_version,
                         "version_verified": False, "profile": CODEX_PROFILE if native else "of-agent-events-v1",
                         "reference": CODEX_REFERENCE if native else None},
            "source_record_count": len(rows), "omitted_record_count": omitted,
            "unmapped_field_count": sum(gap.get("field_count", 0) for gap in gaps),
            "events": events, "event_count": len(events), "gaps": gaps, "network_calls": False,
            "limitations": ["Only the explicitly selected export format is parsed; profiles and private session files are never discovered.",
                            "A request, result or model narrative does not establish an effect on a host.",
                            "Host observations need separately reviewed provenance; shared timestamps do not prove causation.",
                            "Unknown event types, omitted metadata, clipped native text and unmapped fields remain visible as gaps; originals are unchanged.",
                            "Native physical record indices are retained; exporter versions are operator assertions, not authenticated identities."]}
