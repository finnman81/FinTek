"""
Admin routes: usage stats, knowledge gaps, analytics.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.deps import get_current_tenant_id, get_db
from src.api.models.admin import AnalyticsResponse, KnowledgeGapItem, UsageStats
from src.db.models import UsageLog

router = APIRouter()


def _tenant_uuid(tenant_id: str):
    from uuid import UUID
    return UUID(tenant_id)


def _get_usage_stats(tenant_id: str, db: Session) -> UsageStats:
    tid = _tenant_uuid(tenant_id)
    total = db.query(func.count(UsageLog.id)).filter(UsageLog.tenant_id == tid).scalar() or 0
    total_tokens = db.query(func.coalesce(func.sum(UsageLog.tokens_used), 0)).filter(UsageLog.tenant_id == tid).scalar() or 0
    return UsageStats(
        total_queries=total,
        total_tokens=int(total_tokens),
        avg_confidence=0.0,
        low_confidence_queries=0,
    )


@router.get("/usage", response_model=UsageStats)
def usage_stats(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """Aggregate usage stats for the tenant (from usage_logs if populated)."""
    return _get_usage_stats(tenant_id, db)


@router.get("/knowledge-gaps", response_model=List[KnowledgeGapItem])
def knowledge_gaps(
    limit: int = 20,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """Return low-confidence queries (knowledge gaps). Placeholder until we store confidence per query."""
    return []


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """Combined analytics: usage + knowledge gaps."""
    return AnalyticsResponse(
        usage=_get_usage_stats(tenant_id, db),
        knowledge_gaps=[],
    )
