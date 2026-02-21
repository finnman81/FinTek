"""
Chat routes: non-streaming RAG query.
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_current_tenant_id, get_current_user, get_db, get_retrieval_engine
from src.api.models.chat import ChatRequest, ChatResponse, SourceItem
from src.api.usage import check_soft_cap, log_usage
from src.db.models import User
from src.retrieval.engine import RetrievalEngine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    engine: RetrievalEngine = Depends(get_retrieval_engine),
):
    """Run a single RAG query (non-streaming). Logs usage and checks soft cap."""
    try:
        return _chat_impl(body, tenant_id, user, db, engine)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e) or "Chat request failed. Check server logs.")


def _chat_impl(
    body: ChatRequest,
    tenant_id: str,
    user: User,
    db: Session,
    engine: RetrievalEngine,
) -> ChatResponse:
    start = time.perf_counter()
    result = engine.query(question=body.question, conversation_history=None)
    latency_ms = int((time.perf_counter() - start) * 1000)
    tokens = result.usage.get("total_tokens", 0) or result.usage.get("completion_tokens", 0)
    if tokens > 0:
        log_usage(
            session=db,
            tenant_id=tenant_id,
            user_id=str(user.id),
            endpoint="/api/v1/chat",
            model=result.model or "gpt-4o",
            tokens_used=tokens,
            latency_ms=latency_ms,
        )
        check_soft_cap(db, tenant_id)
    sources = [
        SourceItem(
            document=s.get("document", "Unknown"),
            page=str(s["page"]) if s.get("page") else None,
            section=s.get("section"),
            relevance_score=s.get("relevance_score"),
        )
        for s in result.sources
    ]
    return ChatResponse(
        answer=result.answer,
        sources=sources,
        model=result.model,
        confidence=result.confidence,
    )
