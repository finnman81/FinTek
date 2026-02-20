"""
Local cross-encoder reranker for retrieval.

Reranks (query, passage) pairs to improve relevance before context assembly.
Uses sentence-transformers cross-encoder (e.g. ms-marco-MiniLM).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker:
    """Rerank passages by relevance to the query using a local cross-encoder."""

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name)
                logger.info("Loaded reranker model: %s", self.model_name)
            except Exception as e:
                logger.exception("Failed to load cross-encoder %s: %s", self.model_name, e)
                raise
        return self._model

    def rerank(
        self,
        query: str,
        passages: list[str],
        top_n: int = 10,
    ) -> list[tuple[int, float]]:
        """
        Rerank passages by relevance to the query.

        Returns:
            List of (original_index, score) sorted by score descending, length up to top_n.
        """
        if not passages or not query.strip():
            return []
        model = self._get_model()
        pairs = [(query, p) for p in passages]
        try:
            scores = model.predict(pairs)
        except Exception as e:
            logger.warning("Reranker predict failed: %s", e)
            return [(i, 1.0) for i in range(min(top_n, len(passages)))]
        indexed = [(i, float(s)) for i, s in enumerate(scores)]
        indexed.sort(key=lambda x: -x[1])
        return indexed[:top_n]
