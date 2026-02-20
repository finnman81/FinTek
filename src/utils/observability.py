"""
Structured logging and observability.

- JSON logs with tenant_id, request_id, latency_ms for CloudWatch.
- Latency tracking in middleware.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

import structlog


def setup_structured_logging(level: str = "INFO") -> None:
    """Configure structlog for JSON output (CloudWatch-friendly)."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper(), logging.INFO)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)


def log_request(
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    latency_ms: int,
    tenant_id: str | None = None,
    **extra: Any,
) -> None:
    """Emit a structured request log line."""
    payload = {
        "event": "request",
        "request_id": request_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "latency_ms": latency_ms,
    }
    if tenant_id:
        payload["tenant_id"] = tenant_id
    payload.update(extra)
    print(json.dumps(payload), flush=True)
