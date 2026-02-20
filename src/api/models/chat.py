from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = None


class SourceItem(BaseModel):
    document: str
    page: str | None = None
    section: str | None = None
    relevance_score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
    model: str = ""
    confidence: float = 0.0
