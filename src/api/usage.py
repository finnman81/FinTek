"""
Usage tracking: log LLM calls to usage_logs, check soft caps.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from src.db.models import TenantUsageLimits, UsageLog

logger = logging.getLogger(__name__)

# Rough cost per 1k tokens (USD) for logging
COST_PER_1K = {
    "gpt-4o": Decimal("0.005"),
    "gpt-4o-mini": Decimal("0.00015"),
    "text-embedding-3-small": Decimal("0.00002"),
}


def log_usage(
    session: Session,
    tenant_id: str,
    user_id: str | None,
    endpoint: str,
    model: str,
    tokens_used: int,
    latency_ms: int | None = None,
) -> None:
    """Insert one row into usage_logs and optionally update tenant_usage_limits."""
    tid = UUID(tenant_id)
    uid = UUID(user_id) if user_id else None
    cost = (Decimal(tokens_used) / 1000) * COST_PER_1K.get(model, Decimal("0.001"))
    log = UsageLog(
        tenant_id=tid,
        user_id=uid,
        endpoint=endpoint,
        model=model,
        tokens_used=tokens_used,
        cost_estimate=cost,
        latency_ms=latency_ms,
    )
    session.add(log)

    # Update tenant usage limits (current day/month)
    limits = session.query(TenantUsageLimits).filter(TenantUsageLimits.tenant_id == tid).first()
    today = date.today()
    if limits:
        reset_date = limits.last_reset_date.date() if hasattr(limits.last_reset_date, "date") else limits.last_reset_date
        if reset_date != today:
            limits.current_day_tokens = 0
            limits.current_month_tokens = 0
            limits.last_reset_date = today
        limits.current_day_tokens = (limits.current_day_tokens or 0) + tokens_used
        limits.current_month_tokens = (limits.current_month_tokens or 0) + tokens_used
    else:
        session.add(
            TenantUsageLimits(
                tenant_id=tid,
                current_day_tokens=tokens_used,
                current_month_tokens=tokens_used,
                last_reset_date=today,
            )
        )
    # Caller (route) commits via get_db


def check_soft_cap(session: Session, tenant_id: str) -> None:
    """If tenant is over soft cap, log a warning. Does not block."""
    limits = session.query(TenantUsageLimits).filter(TenantUsageLimits.tenant_id == UUID(tenant_id)).first()
    if not limits:
        return
    daily_limit = limits.daily_token_limit
    monthly_limit = limits.monthly_token_limit
    if daily_limit and (limits.current_day_tokens or 0) > daily_limit:
        logger.warning(
            f"Tenant {tenant_id} over daily soft cap: {limits.current_day_tokens} > {daily_limit}"
        )
    if monthly_limit and (limits.current_month_tokens or 0) > monthly_limit:
        logger.warning(
            f"Tenant {tenant_id} over monthly soft cap: {limits.current_month_tokens} > {monthly_limit}"
        )
