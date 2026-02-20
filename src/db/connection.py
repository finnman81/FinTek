"""
Database connection and session management.

Uses SQLAlchemy with a single engine and session factory.
Tenant isolation is logical (tenant_id on all tables), not schema-per-tenant initially.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import load_config
from src.db.models import Base

# Load .env so DATABASE_URL is available (worker, scripts, etc.)
try:
    from dotenv import load_dotenv
    _project_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(_project_root / ".env")
except ImportError:
    pass

_engine = None
_session_factory = None


def get_engine():
    """Create or return the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        config = load_config()
        url = config.database_url
        if not url:
            raise ValueError(
                "DATABASE_URL environment variable is required for production database. "
                "Set it to your PostgreSQL connection string (e.g. postgresql://user:pass@host:5432/dbname)."
            )
        _engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            echo=False,
        )
    return _engine


def get_session_factory():
    """Create or return the session factory."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _session_factory


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
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


def init_db() -> None:
    """Create all tables. Use Alembic migrations in production."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
