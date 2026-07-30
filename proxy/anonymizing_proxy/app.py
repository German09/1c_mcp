from __future__ import annotations

from fastapi import FastAPI, Request
from starlette.responses import Response

from .config import settings
from .forwarder import build_upstream_url, forward_raw
from .anonymizer import Anonymizer, TokenMapper
from .mcp_intercept import (
    safe_json_loads,
    safe_json_dumps,
    make_decision,
    detokenize_tools_call_request,
    anonymize_tools_call_response,
)
from .anonymizer.token_mapper import session_key_from_authorization

app = FastAPI(title="1C MCP Anonymizing Proxy")

_token_mapper = TokenMapper(settings.anonymization_tokenmap_max)
_anonymizer = Anonymizer(
    _token_mapper,
    radical_mode=settings.anonymization_radical_mode,
    ner_enabled=settings.anonymization_ner_enabled,
)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_route(path: str, request: Request) -> Response:
    upstream_url = build_upstream_url(settings.upstream_url, request.url.path)

    body_bytes = await request.body()
    req_json = safe_json_loads(body_bytes)
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    session_id = session_key_from_authorization(auth_header)

    decision = make_decision(
        req_json,
        anonymization_enabled=settings.anonymization_enabled,
        anonymization_tools=settings.anonymization_tools,
    )

    if req_json is not None and decision.should_detokenize:
        # Replace tokens inside arguments so 1C receives real values.
        detok = detokenize_tools_call_request(req_json, session_id, _anonymizer)
        body_bytes = safe_json_dumps(detok)

    status, resp_headers, body = await forward_raw(
        request,
        upstream_url=upstream_url,
        method=request.method,
        timeout_s=settings.timeout,
        body=body_bytes,
    )

    if decision.should_anonymize:
        resp_json = safe_json_loads(body)
        if resp_json is not None:
            anon = anonymize_tools_call_response(resp_json, session_id, _anonymizer)
            body = safe_json_dumps(anon)

    return Response(content=body, status_code=status, headers=resp_headers)

