"""
FastAPI dependencies: database session, current user, tenant, retrieval engine.

Auth is placeholder (header-based) until Clerk is integrated.
"""

from __future__ import annotations

from typing import Annotated, Any, Generator

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from src.core.config import load_config
from src.db.connection import get_session_factory
from src.db.models import Tenant, User
from src.llm.factory import create_embedding_provider, create_llm_provider
from src.retrieval.engine import RetrievalEngine
from src.vectorstore.base import BaseVectorStore
from src.vectorstore.pgvector_store import PostgresVectorStore


def get_config():
    return load_config()


def get_db() -> Generator[Session, None, None]:
    """Yield a database session. Commit on success, rollback on error."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Auth: X-Tenant-ID required; optional Clerk JWT via Authorization: Bearer.
from src.api.auth_clerk import verify_clerk_token


def get_current_tenant_id(
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
    db: Session = Depends(get_db),
) -> str:
    """Extract tenant ID from header. In dev, use DEFAULT_TENANT_SLUG or DEFAULT_TENANT_ID if header missing."""
    if x_tenant_id:
        return x_tenant_id
    import os
    default_id = os.environ.get("DEFAULT_TENANT_ID", "").strip()
    default_slug = os.environ.get("DEFAULT_TENANT_SLUG", "").strip()
    if default_id:
        return default_id
    if default_slug:
        tenant = db.query(Tenant).filter(Tenant.slug == default_slug).first()
        if tenant:
            return str(tenant.id)
    raise HTTPException(status_code=401, detail="X-Tenant-ID header required (or set DEFAULT_TENANT_SLUG / DEFAULT_TENANT_ID in .env for dev)")


def get_current_user(
    request: Request,
    tenant_id: Annotated[str, Depends(get_current_tenant_id)],
    x_user_id: Annotated[str | None, Header(alias="X-User-ID")] = None,
    db: Session = Depends(get_db),
) -> User:
    """Load current user. When Clerk JWT is valid, use sub to lookup or create placeholder."""
    from uuid import UUID

    from src.db.models import Tenant

    try:
        tid = UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-Tenant-ID")

    tenant = db.query(Tenant).filter(Tenant.id == tid).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    clerk_sub: str | None = None
    auth_header = request.headers.get("Authorization")
    payload = verify_clerk_token(auth_header)
    if payload and isinstance(payload.get("sub"), str):
        clerk_sub = payload["sub"]

    user_id = x_user_id
    if clerk_sub:
        user = db.query(User).filter(User.clerk_user_id == clerk_sub, User.tenant_id == tid).first()
        if user:
            return user
        return User(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            tenant_id=tid,
            email=payload.get("email") or "user@clerk",
            role="user",
            clerk_user_id=clerk_sub,
        )
    if user_id:
        try:
            uid = UUID(user_id)
            user = db.query(User).filter(User.id == uid, User.tenant_id == tid).first()
            if user:
                return user
        except ValueError:
            pass

    return User(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        tenant_id=tid,
        email="dev@local",
        role="user",
        clerk_user_id="dev",
    )


def get_vector_store(
    tenant_id: Annotated[str, Depends(get_current_tenant_id)],
    config: Annotated[Any, Depends(get_config)],
) -> BaseVectorStore:
    """Return tenant-scoped vector store. Uses pgvector when provider is pgvector."""
    if getattr(config.vectorstore, "provider", "chroma") == "pgvector":
        factory = get_session_factory()
        return PostgresVectorStore(
            tenant_id=tenant_id,
            session_factory=factory,
            embedding_model=config.embedding.model,
            embedding_version=1,
        )
    # Fallback to Chroma for local dev without Postgres
    from src.vectorstore.chroma_store import ChromaVectorStore
    return ChromaVectorStore(
        collection_name=f"tenant_{tenant_id}",
        persist_directory=config.vectorstore.persist_directory,
        distance_metric=config.vectorstore.distance_metric,
    )


def get_retrieval_engine(
    vector_store: Annotated[BaseVectorStore, Depends(get_vector_store)],
    config: Annotated[Any, Depends(get_config)],
) -> RetrievalEngine:
    """Build retrieval engine with tenant-scoped vector store and optional hybrid/reranker."""
    llm = create_llm_provider(config.llm)
    embedder = create_embedding_provider(config.embedding)
    reranker = None
    if getattr(config.retrieval, "use_reranker", False):
        try:
            from src.retrieval.reranker import CrossEncoderReranker
            model = getattr(config.retrieval, "reranker_model", None) or None
            reranker = CrossEncoderReranker(model_name=model or "cross-encoder/ms-marco-MiniLM-L-6-v2")
        except Exception:
            pass
    return RetrievalEngine(
        llm_provider=llm,
        embedding_provider=embedder,
        vector_store=vector_store,
        top_k=config.retrieval.top_k,
        score_threshold=config.retrieval.score_threshold,
        use_hybrid=getattr(config.retrieval, "use_hybrid", False),
        vector_top_k=getattr(config.retrieval, "vector_top_k", 40),
        lexical_top_k=getattr(config.retrieval, "lexical_top_k", 40),
        rrf_k=getattr(config.retrieval, "rrf_k", 60),
        final_k=getattr(config.retrieval, "final_k", 20),
        ef_search=getattr(config.retrieval, "ef_search", 80),
        use_reranker=getattr(config.retrieval, "use_reranker", False),
        rerank_top_n=getattr(config.retrieval, "rerank_top_n", 30),
        final_context_chunks=getattr(config.retrieval, "final_context_chunks", 8),
        use_two_pass_answer=getattr(config.retrieval, "use_two_pass_answer", False),
        reranker=reranker,
    )
