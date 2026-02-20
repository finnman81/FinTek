"""
Middleware: request context, structured logging (JSON), latency tracking.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Add request_id, start_time, and tenant_id (from header) to request state for logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state.request_id = str(uuid.uuid4())[:8]
        request.state.start_time = time.perf_counter()
        request.state.tenant_id = request.headers.get("X-Tenant-ID")
        response = await call_next(request)
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Structured JSON logging: request_id, method, path, status, latency_ms, tenant_id (when available)."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = getattr(request.state, "request_id", "")
        start = getattr(request.state, "start_time", time.perf_counter())
        response = await call_next(request)
        latency_ms = int((time.perf_counter() - start) * 1000)
        tenant_id = getattr(request.state, "tenant_id", None)
        payload = {
            "event": "request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        }
        if tenant_id:
            payload["tenant_id"] = tenant_id
        print(json.dumps(payload), flush=True)
        return response
