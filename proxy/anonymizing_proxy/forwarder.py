from __future__ import annotations

from typing import Mapping
import httpx
from fastapi import Request


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


def filter_headers(headers: Mapping[str, str]) -> dict[str, str]:
    # Keep client-provided headers (notably Authorization), but remove hop-by-hop ones.
    out: dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in HOP_BY_HOP_HEADERS:
            continue
        out[k] = v
    return out


def build_upstream_url(upstream_base: str, request_path: str) -> str:
    base = upstream_base.rstrip("/")
    rel = request_path.lstrip("/")
    if not rel:
        return base
    return f"{base}/{rel}"


async def forward_raw(
    request: Request,
    *,
    upstream_url: str,
    method: str,
    timeout_s: float,
    body: bytes | None = None,
) -> tuple[int, dict[str, str], bytes]:
    if body is None:
        body = await request.body()

    async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=False) as client:
        resp = await client.request(
            method=method,
            url=upstream_url,
            params=request.query_params,
            content=body if body else None,
            headers=filter_headers(request.headers),
        )

    # Response headers to return (without hop-by-hop).
    resp_headers: dict[str, str] = {}
    for k, v in resp.headers.items():
        lk = k.lower()
        if lk in HOP_BY_HOP_HEADERS:
            continue
        resp_headers[k] = v

    return resp.status_code, resp_headers, resp.content

