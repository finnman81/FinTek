"""
SQLite-based query logging for analytics.

Stores every user query, the generated response, source documents used,
and metadata for building usage analytics and knowledge gap detection.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class QueryStore:
    """Lightweight SQLite store for query analytics."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    sources TEXT,
                    model TEXT,
                    tokens_used INTEGER DEFAULT 0,
                    confidence REAL DEFAULT 0.0,
                    session_id TEXT,
                    feedback INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_queries_timestamp
                ON queries(timestamp)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_type TEXT,
                    ingested_at TEXT NOT NULL,
                    total_chunks INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active'
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def log_query(
        self,
        question: str,
        answer: str,
        sources: list[dict[str, Any]] | None = None,
        model: str = "",
        tokens_used: int = 0,
        confidence: float = 0.0,
        session_id: str = "",
    ) -> int:
        """Log a query-response pair. Returns the row ID."""
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO queries
                   (timestamp, question, answer, sources, model, tokens_used, confidence, session_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    datetime.now(timezone.utc).isoformat(),
                    question,
                    answer,
                    json.dumps(sources or []),
                    model,
                    tokens_used,
                    confidence,
                    session_id,
                ),
            )
            return cursor.lastrowid or 0

    def log_document(self, filename: str, file_type: str, total_chunks: int) -> int:
        """Log a document ingestion event. Returns the row ID."""
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO documents (filename, file_type, ingested_at, total_chunks)
                   VALUES (?, ?, ?, ?)""",
                (filename, file_type, datetime.now(timezone.utc).isoformat(), total_chunks),
            )
            return cursor.lastrowid or 0

    def get_recent_queries(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get most recent queries for the admin dashboard."""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM queries ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_query_stats(self) -> dict[str, Any]:
        """Get aggregate query statistics."""
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM queries").fetchone()[0]
            avg_confidence = conn.execute(
                "SELECT AVG(confidence) FROM queries WHERE confidence > 0"
            ).fetchone()[0]
            total_tokens = conn.execute(
                "SELECT SUM(tokens_used) FROM queries"
            ).fetchone()[0]
            low_confidence = conn.execute(
                "SELECT COUNT(*) FROM queries WHERE confidence < 0.5"
            ).fetchone()[0]

            return {
                "total_queries": total,
                "avg_confidence": round(avg_confidence or 0, 3),
                "total_tokens": total_tokens or 0,
                "low_confidence_queries": low_confidence,
            }

    def get_knowledge_gaps(self, limit: int = 20) -> list[dict[str, Any]]:
        """Find queries with low confidence — potential knowledge gaps."""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT question, confidence, timestamp
                   FROM queries
                   WHERE confidence < 0.5
                   ORDER BY confidence ASC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_documents(self) -> list[dict[str, Any]]:
        """Get all ingested documents."""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY ingested_at DESC"
            ).fetchall()
            return [dict(row) for row in rows]
