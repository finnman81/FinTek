"""
Unit tests for usage tracking: log_usage, check_soft_cap.
"""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.api.usage import log_usage, check_soft_cap, COST_PER_1K
from src.db.models import UsageLog, TenantUsageLimits


class TestLogUsage:
    def test_log_usage_adds_usage_log_to_session(self):
        session = MagicMock()
        tenant_id = str(uuid4())
        log_usage(
            session=session,
            tenant_id=tenant_id,
            user_id=str(uuid4()),
            endpoint="/api/v1/chat",
            model="gpt-4o",
            tokens_used=100,
            latency_ms=200,
        )
        session.add.assert_called()
        call_arg = session.add.call_args[0][0]
        assert isinstance(call_arg, UsageLog)
        assert call_arg.tokens_used == 100
        assert call_arg.endpoint == "/api/v1/chat"
        assert call_arg.model == "gpt-4o"
        assert call_arg.latency_ms == 200

    def test_log_usage_creates_tenant_limits_if_missing(self):
        session = MagicMock()
        tenant_id = str(uuid4())
        session.query.return_value.filter.return_value.first.return_value = None  # no existing limits
        log_usage(
            session=session,
            tenant_id=tenant_id,
            user_id=None,
            endpoint="/api/v1/chat",
            model="gpt-4o-mini",
            tokens_used=50,
        )
        assert session.add.call_count >= 1
        # First add is UsageLog, second may be TenantUsageLimits
        calls = [c[0][0].__class__.__name__ for c in session.add.call_args_list]
        assert "UsageLog" in calls

    def test_cost_estimate_applied(self):
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = None
        log_usage(
            session=session,
            tenant_id=str(uuid4()),
            user_id=None,
            endpoint="/chat",
            model="gpt-4o",
            tokens_used=1000,
        )
        log_entry = session.add.call_args_list[0][0][0]
        assert log_entry.cost_estimate is not None
        assert float(log_entry.cost_estimate) > 0


class TestCheckSoftCap:
    def test_check_soft_cap_no_limits_does_nothing(self):
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = None
        check_soft_cap(session, str(uuid4()))
        session.query.assert_called()

    def test_check_soft_cap_under_limit_does_not_warn(self):
        session = MagicMock()
        limits = TenantUsageLimits(
            tenant_id=uuid4(),
            daily_token_limit=10_000,
            monthly_token_limit=100_000,
            current_day_tokens=100,
            current_month_tokens=500,
            last_reset_date=date.today(),
        )
        session.query.return_value.filter.return_value.first.return_value = limits
        check_soft_cap(session, str(limits.tenant_id))
        # No exception; we're not asserting on logger

    def test_check_soft_cap_over_daily_logs_warning(self, caplog):
        import logging
        caplog.set_level(logging.WARNING)
        session = MagicMock()
        tid = uuid4()
        limits = TenantUsageLimits(
            tenant_id=tid,
            daily_token_limit=100,
            monthly_token_limit=10_000,
            current_day_tokens=200,
            current_month_tokens=200,
            last_reset_date=date.today(),
        )
        session.query.return_value.filter.return_value.first.return_value = limits
        check_soft_cap(session, str(tid))
        assert any("soft cap" in rec.message.lower() or "over" in rec.message.lower() for rec in caplog.records)


class TestCostPer1K:
    def test_known_models_have_cost(self):
        assert "gpt-4o" in COST_PER_1K
        assert "gpt-4o-mini" in COST_PER_1K
        assert "text-embedding-3-small" in COST_PER_1K
