"""
Anchorpoint — Streamlit chat UI.

Single-page, mobile-first interface: chat + sidebar (upload, admin).
Streaming responses, multi-turn conversation, sticky input.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env if present (OPENAI_API_KEY, etc.)
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass

import streamlit as st

from src.core.config import load_config
from src.llm.factory import create_llm_provider, create_embedding_provider
from src.vectorstore.chroma_store import ChromaVectorStore
from src.retrieval.engine import RetrievalEngine
from src.utils.logger import setup_logging
from src.utils.query_store import QueryStore
from src.ingestion.pipeline import IngestionPipeline
from src.ui.components.chat_message import render_chat_message
from src.ui.components.sidebar import render_sidebar


def _mobile_css() -> str:
    """Mobile-first: larger touch targets, full viewport, sticky input."""
    return """
    <style>
    /* Sticky chat input at bottom */
    .stTextInput > div > div > input {
        font-size: 1rem;
        min-height: 48px;
    }
    /* Reduce padding on small screens */
    @media (max-width: 768px) {
        .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    }
    /* Ensure main content uses space */
    section.main .block-container { max-width: 100%; }
    </style>
    """


@st.cache_resource
def _get_services():
    """Load config and create LLM, vector store, retrieval engine, query store, ingestion (cached)."""
    config = load_config()
    setup_logging(level=config.log_level)

    llm = create_llm_provider(config.llm)
    embedder = create_embedding_provider(config.embedding)
    vector_store = ChromaVectorStore(
        collection_name=config.vectorstore.collection_name,
        persist_directory=config.vectorstore.persist_directory,
        distance_metric=config.vectorstore.distance_metric,
    )
    engine = RetrievalEngine(
        llm_provider=llm,
        embedding_provider=embedder,
        vector_store=vector_store,
        top_k=config.retrieval.top_k,
        score_threshold=config.retrieval.score_threshold,
    )
    query_store = QueryStore(config.query_log_db)
    pipeline = IngestionPipeline(
        embedding_provider=embedder,
        vector_store=vector_store,
        chunk_size=config.ingestion.chunk_size,
        chunk_overlap=config.ingestion.chunk_overlap,
        raw_storage_dir=config.ingestion.raw_data_dir,
    )
    return config, engine, query_store, pipeline, vector_store


def main() -> None:
    st.set_page_config(
        page_title="Anchorpoint",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    config, engine, query_store, pipeline, vector_store = _get_services()
    branding = config.branding

    # Session state: messages for multi-turn chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())[:8]

    def on_new_chat() -> None:
        st.session_state.messages = []
        st.rerun()

    # Sidebar
    render_sidebar(
        config=config,
        query_store=query_store,
        ingestion_pipeline=pipeline,
        vector_store=vector_store,
        on_new_chat=on_new_chat,
    )

    # Mobile-friendly CSS
    st.markdown(_mobile_css(), unsafe_allow_html=True)

    # Header (product + customer)
    title = branding.product_name or "Anchorpoint"
    sub = f"for {branding.customer_name}" if branding.customer_name else ""
    st.title(title)
    if sub:
        st.caption(sub)

    # Chat history
    for i, msg in enumerate(st.session_state.messages):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        sources = msg.get("sources") if role == "assistant" else None
        render_chat_message(role, content, sources=sources, key_prefix=f"msg_{i}")

    # Chat input (sticky at bottom in practice via Streamlit layout)
    prompt = st.chat_input("Ask a question...")
    if prompt:
        # Append user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Build conversation history for context (last 6 turns)
        history = []
        for m in st.session_state.messages[:-1]:
            if m.get("role") in ("user", "assistant"):
                history.append({"role": m["role"], "content": m.get("content", "")})

        # Stream response into a placeholder
        placeholder = st.empty()
        with placeholder.container():
            stream_placeholder = st.empty()
            accumulated = []
            token_stream, sources = engine.query_stream(
                question=prompt,
                conversation_history=history[-6:] if history else None,
            )
            for token in token_stream:
                accumulated.append(token)
                stream_placeholder.markdown("".join(accumulated))

            full_answer = "".join(accumulated)

        # Persist assistant message (rerun will render full history with Sources)
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_answer,
            "sources": sources,
        })

        # Log query for analytics
        query_store.log_query(
            question=prompt,
            answer=full_answer,
            sources=sources,
            model="",
            tokens_used=0,
            confidence=0.0,
            session_id=st.session_state.session_id,
        )

        st.rerun()


if __name__ == "__main__":
    main()
