"""
Sidebar with branding, document upload, and admin sections.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import streamlit as st

from src.core.config import AppConfig, BrandingConfig


def render_sidebar(
    config: AppConfig,
    query_store: Any,
    ingestion_pipeline: Any,
    vector_store: Any,
    on_new_chat: Callable[[], None],
) -> None:
    """
    Render the app sidebar: branding, upload, admin, and new conversation.

    Args:
        config: Application configuration (branding, ingestion, etc.).
        query_store: QueryStore instance for admin stats.
        ingestion_pipeline: IngestionPipeline for document uploads.
        vector_store: Vector store (for document count).
        on_new_chat: Callback when user clicks New Conversation.
    """
    with st.sidebar:
        _render_branding(config.branding)
        st.divider()

        if st.button("New conversation", use_container_width=True):
            on_new_chat()

        st.divider()

        with st.expander("Upload documents", expanded=False):
            _render_upload(config, ingestion_pipeline, query_store)

        with st.expander("Admin", expanded=False):
            _render_admin(query_store, vector_store)


def _render_branding(branding: BrandingConfig) -> None:
    """Show product name, customer name, and optional logo."""
    product = branding.product_name or "Munitor AI"
    customer = branding.customer_name or ""

    logo_path = branding.customer_logo
    if logo_path and Path(logo_path).exists():
        st.image(logo_path, use_container_width=True)

    st.markdown(f"**{product}**")
    if customer:
        st.caption(f"for {customer}")

    if branding.accent_color:
        st.markdown(
            f'<div style="height:3px; background:{branding.accent_color}; border-radius:2px;"></div>',
            unsafe_allow_html=True,
        )


def _render_upload(
    config: AppConfig,
    pipeline: Any,
    query_store: Any,
) -> None:
    """File uploader and ingestion trigger."""
    extensions = config.ingestion.supported_extensions
    accept = [e.lstrip(".") for e in extensions]

    uploaded = st.file_uploader(
        "Choose files",
        type=accept,
        accept_multiple_files=True,
        key="sidebar_uploader",
    )

    if not uploaded:
        return

    if st.button("Ingest selected files", key="ingest_btn"):
        import tempfile
        from pathlib import Path

        for f in uploaded:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(f.name).suffix) as tmp:
                tmp.write(f.getvalue())
                path = Path(tmp.name)
            try:
                result = pipeline.ingest_file(path)
                if result.status == "success":
                    query_store.log_document(
                        result.filename,
                        result.file_type,
                        result.total_chunks,
                    )
                    st.success(f"**{result.filename}**: {result.total_chunks} chunks ingested.")
                else:
                    st.error(f"**{result.filename}**: {result.error_message}")
            except Exception as e:
                st.error(f"**{f.name}**: {e}")
            finally:
                path.unlink(missing_ok=True)


def _render_admin(query_store: Any, vector_store: Any) -> None:
    """Query stats, document list, knowledge gaps."""
    try:
        stats = query_store.get_query_stats()
        st.metric("Total queries", stats["total_queries"])
        st.metric("Avg confidence", stats["avg_confidence"])
        st.metric("Low-confidence queries", stats["low_confidence_queries"])
    except Exception:
        st.caption("No query data yet.")

    st.divider()
    st.subheader("Documents")
    try:
        doc_count = vector_store.count()
        st.metric("Chunks in knowledge base", doc_count)
    except Exception:
        doc_count = 0
        st.caption("Vector store not loaded.")

    try:
        docs = query_store.get_documents()
        if docs:
            for d in docs[:10]:
                st.caption(f"• {d.get('filename', '?')} ({d.get('total_chunks', 0)} chunks)")
        else:
            st.caption("No documents logged yet.")
    except Exception:
        st.caption("No document log.")

    st.divider()
    st.subheader("Knowledge gaps")
    try:
        gaps = query_store.get_knowledge_gaps(limit=5)
        if gaps:
            for g in gaps:
                st.caption(f"• {g.get('question', '')[:60]}... (conf: {g.get('confidence', 0):.2f})")
        else:
            st.caption("No low-confidence queries yet.")
    except Exception:
        st.caption("No gap data.")
