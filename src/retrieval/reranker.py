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


def _default_device() -> str:
    """Default device: prefer CUDA if available, otherwise CPU."""
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


class CrossEncoderReranker:
    """Rerank passages by relevance to the query using a local cross-encoder."""

    def __init__(self, model_name: str = DEFAULT_MODEL, device: str | None = None):
        self.model_name = model_name
        self._device = device
        self._model = None
        self._device_used = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder
            
            # Use explicit device if provided, otherwise auto-detect (prefer GPU)
            device = self._device if self._device is not None else _default_device()
            
            # Try GPU first, fall back to CPU on error
            try:
                self._model = CrossEncoder(self.model_name, device=device)
                self._device_used = device
                logger.info("Loaded reranker model: %s (device=%s)", self.model_name, device)
            except Exception as e:
                # If GPU fails (e.g., unsupported CUDA version), try CPU
                if device == "cuda":
                    logger.warning(
                        "Failed to load reranker on CUDA (%s), falling back to CPU", e
                    )
                    try:
                        self._model = CrossEncoder(self.model_name, device="cpu")
                        self._device_used = "cpu"
                        logger.info("Loaded reranker model: %s (device=cpu)", self.model_name)
                    except Exception as cpu_error:
                        logger.exception("Failed to load cross-encoder on CPU: %s", cpu_error)
                        raise
                else:
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
            # If prediction fails on GPU (e.g., CUDA kernel error), try CPU
            error_msg = str(e).lower()
            if self._device_used == "cuda" and ("cuda" in error_msg or "kernel" in error_msg):
                logger.warning(
                    "Reranker predict failed on CUDA (%s), recreating model on CPU", e
                )
                try:
                    from sentence_transformers import CrossEncoder
                    self._model = CrossEncoder(self.model_name, device="cpu")
                    self._device_used = "cpu"
                    scores = self._model.predict(pairs)
                    logger.info("Reranker now using CPU device")
                except Exception as cpu_error:
                    logger.warning("Reranker predict failed on CPU too: %s", cpu_error)
                    return [(i, 1.0) for i in range(min(top_n, len(passages)))]
            else:
                logger.warning("Reranker predict failed: %s", e)
                return [(i, 1.0) for i in range(min(top_n, len(passages)))]
        indexed = [(i, float(s)) for i, s in enumerate(scores)]
        indexed.sort(key=lambda x: -x[1])
        return indexed[:top_n]
