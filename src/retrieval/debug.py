"""
Debug tracing logic extracted from RetrievalEngine.

Appends query trace records to a JSONL file when RAG_DEBUG_TRACE=1.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


def append_debug_trace(payload: dict[str, Any], trace_path: Path) -> None:
    """Append one query trace record to JSONL."""
    try:
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        with trace_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception as e:
        logger.warning("Failed to write RAG debug trace", error=str(e))
