from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .anonymizer import Anonymizer


@dataclass(frozen=True)
class ToolsCallDecision:
    should_detokenize: bool
    should_anonymize: bool
    tool_name: str | None


def safe_json_loads(body: bytes) -> Any | None:
    if not body:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return None


def safe_json_dumps(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def get_tools_call_tool_name(req_json: Any) -> str | None:
    if not isinstance(req_json, dict):
        return None
    if req_json.get("method") != "tools/call":
        return None
    params = req_json.get("params") or {}
    if not isinstance(params, dict):
        return None
    name = params.get("name")
    if isinstance(name, str):
        return name
    return None


def make_decision(
    req_json: Any,
    *,
    anonymization_enabled: bool,
    anonymization_tools: set[str],
) -> ToolsCallDecision:
    tool_name = get_tools_call_tool_name(req_json)
    should = bool(anonymization_enabled and tool_name and tool_name in anonymization_tools)
    return ToolsCallDecision(
        should_detokenize=should,
        should_anonymize=should,
        tool_name=tool_name,
    )


def detokenize_tools_call_request(
    req_json: dict[str, Any],
    session_id: str,
    anonymizer: Anonymizer,
) -> dict[str, Any]:
    params = req_json.get("params") or {}
    if not isinstance(params, dict):
        return req_json

    arguments = params.get("arguments")
    if arguments is None:
        return req_json

    if not isinstance(arguments, (dict, list, str, int, float, bool)):
        return req_json

    params["arguments"] = anonymizer.detokenize_in_obj(session_id, arguments)
    req_json["params"] = params
    return req_json


def anonymize_tools_call_response(
    resp_json: Any,
    session_id: str,
    anonymizer: Anonymizer,
) -> Any:
    if not isinstance(resp_json, dict):
        return resp_json

    result = resp_json.get("result")
    if not isinstance(result, dict):
        return resp_json

    if result.get("isError") is True:
        return resp_json

    content = result.get("content")
    if not isinstance(content, list):
        return resp_json

    for element in content:
        if not isinstance(element, dict):
            continue
        if element.get("type") != "text":
            continue
        if "text" not in element:
            continue

        text = element.get("text")
        if not isinstance(text, str):
            continue

        element["text"] = anonymizer.anonymize_string(session_id, text, key_hint=None)

    return resp_json

