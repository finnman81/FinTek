"""
Anchorpoint FastAPI application.

Run with: uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware import LoggingMiddleware, RequestContextMiddleware
from src.api.routes import admin, auth, chat, documents, feedback


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown: load config, ensure DB connectivity (optional)."""
    yield


app = FastAPI(
    title="Anchorpoint API",
    description="RAG and document ingestion API for Anchorpoint.",
    version="1.0.0",
    lifespan=lifespan,
)

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
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected", "detail": str(e)},
        )
