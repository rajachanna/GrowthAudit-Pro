"""Mount the GrowthAudit scanner into the existing NextGen FastAPI backend.

Only the public HTTP API adapter is imported here; the CLI audit engine stays
in GrowthAudit-Pro. Add `app.include_router(router)` in the hosting backend.
Requires the host application's FastAPI dependency.
"""
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import Response

from growthaudit.serverless import handle_request

router = APIRouter()


async def _body_with_limit(request: Request, maximum: int = 4096):
    """Reject oversized *streamed* requests before buffering them."""
    try:
        length = int(request.headers.get("content-length", "0"))
    except ValueError:
        return None
    if length > maximum or length < 0:
        return None
    chunks = bytearray()
    async for data in request.stream():
        if len(chunks) + len(data) > maximum:
            return None
        chunks.extend(data)
    return bytes(chunks)


@router.api_route("/api/growth-audit", methods=["GET", "POST"])
@router.api_route("/api/growth-audit/health", methods=["GET"])
async def growth_audit(request: Request):
    if request.method == "POST":
        if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
            return Response(b'{"error":"unsupported_media_type"}', status_code=415, media_type="application/json")
        body = await _body_with_limit(request)
        if body is None:
            return Response(b'{"error":"request_too_large"}', status_code=413, media_type="application/json")
    else:
        body = b""

    # Isolate blocking DNS/TLS retrieval from FastAPI's async event loop.
    status, payload = await asyncio.to_thread(
        handle_request, request.method, request.url.path, body
    )
    return Response(
        content=payload,
        status_code=status,
        media_type="application/json",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
