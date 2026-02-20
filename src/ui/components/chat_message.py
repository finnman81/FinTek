"""
Chat message bubble renderer with collapsible source citations.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_chat_message(
    role: str,
    content: str,
    sources: list[dict[str, Any]] | None = None,
    key_prefix: str = "",
) -> None:
    """
    Render a single chat message (user or assistant) with optional sources.

    Args:
        role: "user" or "assistant"
        content: Message text (supports markdown).
        sources: List of source dicts with keys like document, page, section, relevance_score.
        key_prefix: Unique prefix for Streamlit widget keys (e.g. message index).
    """
    if role == "user":
        with st.container():
            st.markdown("**You**")
            st.markdown(content)
        return

    # Assistant message
    with st.container():
        st.markdown("**Assistant**")
        st.markdown(content)

    if sources:
        with st.expander(f"Sources ({len(sources)})", expanded=False):
            for src in sources:
                doc = src.get("document", "Unknown")
                page = src.get("page", "")
                section = src.get("section", "")
                score = src.get("relevance_score", 0)
                parts = [doc]
                if page:
                    parts.append(f"p.{page}")
                if section:
                    parts.append(section)
                if score:
                    parts.append(f"relevance: {score:.2f}")
                st.caption(" | ".join(str(p) for p in parts))
