"""
Feedback route: submit a 1-5 rating for a chat response. Data used for refinement.
Stores in DB; on DB failure appends to data/logs/feedback.log as fallback.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.deps import get_current_tenant_id, get_db
from src.db.models import ResponseRating

logger = logging.getLogger(__name__)

router = APIRouter()

# Fallback log for when DB is unavailable (e.g. migration not run)
FEEDBACK_LOG_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "logs" / "feedback.log"


def _append_feedback_log(tenant_id: str, question: str, rating: int, answer: str | None) -> None:
    """Append one rating to a file so we don't lose data if DB fails."""
    try:
        FEEDBACK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        snippet_q = (question[:200] + "...") if len(question) > 200 else question
        snippet_a = (answer[:200] + "...") if (answer and len(answer) > 200) else (answer or "")
        line = f"tenant={tenant_id}\trating={rating}\tquestion={snippet_q}\tanswer={snippet_a}\n"
        with open(FEEDBACK_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        logger.exception("Failed to write feedback fallback log: %s", e)


class FeedbackRequest(BaseModel):
    question: str
    rating: int = Field(..., ge=1, le=5, description="1-5")
    answer: str | None = None


class FeedbackResponse(BaseModel):
    ok: bool = True


@router.post("", response_model=FeedbackResponse)
def submit_feedback(
    body: FeedbackRequest,
    tenant_id: Annotated[str, Depends(get_current_tenant_id)],
    db: Session = Depends(get_db),
):
    """Store a 1-5 rating for a chat Q&A. Logs to DB; on failure appends to data/logs/feedback.log."""
    from uuid import UUID

    try:
        tid = UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID")

    record = ResponseRating(
        tenant_id=tid,
        question=body.question,
        rating=body.rating,
        answer=body.answer,
    )
    db.add(record)
    try:
        db.commit()
        logger.info(
            "Feedback saved: tenant_id=%s rating=%s question_len=%s",
            tenant_id,
            body.rating,
            len(body.question),
        )
        return FeedbackResponse()
    except Exception as e:
        db.rollback()
        logger.exception("Feedback DB save failed: %s", e)
        _append_feedback_log(tenant_id, body.question, body.rating, body.answer)
        raise HTTPException(
            status_code=500,
            detail="Rating could not be saved to the database. It was logged to a file for recovery.",
        )
