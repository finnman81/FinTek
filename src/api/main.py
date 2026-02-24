"""
Anchorpoint FastAPI application.

Run with: uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

# Load .env as soon as the API module is loaded (any startup path: app.py, uvicorn, etc.)
try:
    from dotenv import load_dotenv
    _api_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(_api_root / ".env")
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.middleware import LoggingMiddleware, RequestContextMiddleware
from src.api.routes import admin, auth, chat, documents, feedback

logger = logging.getLogger(__name__)


async def global_exception_handler(request, exc: Exception):
    """Return 500 with a clear detail message so the UI can show it."""
    try:
        logger.exception("Unhandled exception: %s", exc)
        detail = str(exc) if str(exc) else "Internal server error. Check server logs."
        return JSONResponse(
            status_code=500,
            content={"detail": detail},
        )
    except Exception as fallback:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Check server logs."},
        )


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
app.add_exception_handler(Exception, global_exception_handler)

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


@app.get("/api/v1/health/chat")
def api_health_chat():
    """
    Diagnostic: run the same dependency chain as POST /api/v1/chat.
    Returns 200 if ready for chat, or 503 with detail showing what's broken.
    Call with X-Tenant-ID header (or set DEFAULT_TENANT_ID in .env).
    """
    try:
        from src.core.config import load_config
        from src.db.connection import get_session_factory
        from src.db.models import Tenant
        from src.llm.factory import create_llm_provider, create_embedding_provider
        from src.vectorstore.pgvector_store import PostgresVectorStore

        config = load_config()
        tenant_id = __import__("os").environ.get("DEFAULT_TENANT_ID", "").strip()
        if not tenant_id:
            return JSONResponse(
                status_code=503,
                content={"detail": "DEFAULT_TENANT_ID or X-Tenant-ID required. Set DEFAULT_TENANT_ID in .env for dev."},
            )

        factory = get_session_factory()
        session = factory()
        try:
            from uuid import UUID
            tid = UUID(tenant_id)
            tenant = session.query(Tenant).filter(Tenant.id == tid).first()
            if not tenant:
                return JSONResponse(
                    status_code=503,
                    content={"detail": f"Tenant {tenant_id} not found in database. Run migrations and seed."},
                )
        finally:
            session.close()

        llm = create_llm_provider(config.llm)
        embedder = create_embedding_provider(config.embedding)
        store = PostgresVectorStore(
            tenant_id=tenant_id,
            session_factory=factory,
            embedding_model=config.embedding.model,
            embedding_version=1,
        )
        _ = store.count()
        return {"status": "ok", "message": "Chat dependencies ready (DB, tenant, LLM, embedder, vector store)."}
    except Exception as e:
        logger.exception("Health chat check failed: %s", e)
        return JSONResponse(
            status_code=503,
            content={"detail": str(e)},
        )
