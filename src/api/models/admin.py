from __future__ import annotations

from pydantic import BaseModel


class UsageStats(BaseModel):
    total_queries: int
    total_tokens: int
    avg_confidence: float
    low_confidence_queries: int


class KnowledgeGapItem(BaseModel):
    question: str
    confidence: float
    timestamp: str


class AnalyticsResponse(BaseModel):
    usage: UsageStats
    knowledge_gaps: list[KnowledgeGapItem]
