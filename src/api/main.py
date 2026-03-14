"""
Munitor AI FastAPI application.

Run with: uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.api.middleware import LoggingMiddleware, RequestContextMiddleware
from src.api.routes import admin, auth, chat, documents, feedback


def _key_func(request: Request) -> str:
    """Rate-limit key: tenant ID if present, else IP."""
    tenant = request.headers.get("X-Tenant-ID")
    if tenant:
        return f"tenant:{tenant}"
    return get_remote_address(request)


limiter = Limiter(key_func=_key_func, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown: load config, ensure DB connectivity (optional)."""
    yield


app = FastAPI(
    title="Munitor AI API",
    description="RAG and document ingestion API for Munitor AI.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestContextMiddleware)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["feedback"])


@app.get("/health")
def health():
    """Shallow health check (no DB). Use for load balancer liveness."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/v1/health")
def api_health():
    """Shallow health check (no DB)."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/v1/health/db")
def api_health_db():
    """Deep health check: DB connectivity. Returns 503 if DB is down."""
    try:
        from sqlalchemy import text
        from src.db.connection import get_session_factory
        session_factory = get_session_factory()
        session = session_factory()
        try:
            session.execute(text("SELECT 1"))
            return {"status": "ok", "database": "connected"}
        finally:
            session.close()
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected", "detail": str(e)},
        )
