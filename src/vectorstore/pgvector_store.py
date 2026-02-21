"""
Postgres + pgvector implementation of the vector store.

Stores embeddings in the document_chunks table. Tenant-scoped.
Implements BaseVectorStore so RetrievalEngine and ingestion can use it
interchangeably with ChromaDB or Pinecone.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.vectorstore.base import BaseVectorStore, SearchResult

logger = logging.getLogger(__name__)


class PostgresVectorStore(BaseVectorStore):
    """Postgres + pgvector vector store. Tenant-scoped, uses document_chunks table."""

    def __init__(
        self,
        tenant_id: str,
        session_factory: Any,
        embedding_model: str = "text-embedding-3-small",
        embedding_version: int = 1,
    ):
        self.tenant_id = tenant_id
        self._session_factory = session_factory
        self.embedding_model = embedding_model
        self.embedding_version = embedding_version

    def _session(self) -> Session:
        return self._session_factory()

    def add_parents(
        self,
        document_id: str,
        parents: list[dict[str, Any]],
    ) -> list[str]:
        """Insert parent records into document_parents; return list of parent IDs."""
        if not parents:
            return []
        session = self._session()
        inserted = []
        try:
            for p in parents:
                parent_id = str(uuid.uuid4())
                text_parent = p.get("text_parent", "")
                session.execute(
                    text("""
                        INSERT INTO document_parents
                        (id, document_id, tenant_id, section_path, text_parent, page_start, page_end, metadata, tsv)
                        VALUES
                        (:id, CAST(:document_id AS uuid), CAST(:tenant_id AS uuid), :section_path, :text_parent,
                         :page_start, :page_end, CAST(:metadata AS jsonb), to_tsvector('english', coalesce(:text_parent, '')))
                    """),
                    {
                        "id": parent_id,
                        "document_id": document_id,
                        "tenant_id": self.tenant_id,
                        "section_path": p.get("section_path"),
                        "text_parent": text_parent,
                        "page_start": p.get("page_start"),
                        "page_end": p.get("page_end"),
                        "metadata": json.dumps(p.get("metadata") or {}),
                    },
                )
                inserted.append(parent_id)
            session.commit()
            logger.info(f"Added {len(parents)} parents to pgvector for tenant {self.tenant_id}")
            return inserted
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def add_documents(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        if not texts:
            return []

        metadatas = metadatas or [{} for _ in texts]
        ids = ids or [str(uuid.uuid4()) for _ in texts]

        session = self._session()
        try:
            inserted_ids = []
            for i, (text_val, embedding, meta) in enumerate(zip(texts, embeddings, metadatas)):
                doc_id = meta.get("document_id")
                chunk_index = meta.get("chunk_index", i)
                if not doc_id:
                    raise ValueError("metadata must include 'document_id' for PostgresVectorStore")

                chunk_id = ids[i] if i < len(ids) else str(uuid.uuid4())
                embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
                meta_for_json = {k: v for k, v in meta.items() if k not in (
                    "document_id", "chunk_index", "section_path", "page_start", "page_end",
                    "content_type", "part_numbers", "error_codes", "model_number", "parent_id",
                )}
                part_numbers = meta.get("part_numbers")
                error_codes = meta.get("error_codes")
                session.execute(
                    text("""
                        INSERT INTO document_chunks
                        (id, document_id, tenant_id, chunk_index, text, embedding, embedding_model, embedding_version,
                         metadata, section_path, page_start, page_end, content_type, part_numbers, error_codes, model_number, parent_id, tsv, created_at)
                        VALUES
                        (:id, CAST(:document_id AS uuid), CAST(:tenant_id AS uuid), :chunk_index, :text, CAST(:embedding AS vector),
                         :embedding_model, :embedding_version, CAST(:metadata AS jsonb), :section_path, :page_start, :page_end,
                         :content_type, :part_numbers, :error_codes, :model_number, CAST(:parent_id AS uuid), to_tsvector('english', coalesce(:text, '')), now())
                    """),
                    {
                        "id": chunk_id,
                        "document_id": str(doc_id),
                        "tenant_id": self.tenant_id,
                        "chunk_index": chunk_index,
                        "text": text_val,
                        "embedding": embedding_str,
                        "embedding_model": self.embedding_model,
                        "embedding_version": self.embedding_version,
                        "metadata": json.dumps(meta_for_json) if meta_for_json else "{}",
                        "section_path": meta.get("section_path"),
                        "page_start": meta.get("page_start"),
                        "page_end": meta.get("page_end"),
                        "content_type": meta.get("content_type"),
                        "part_numbers": part_numbers if isinstance(part_numbers, list) else ([part_numbers] if part_numbers else None),
                        "error_codes": error_codes if isinstance(error_codes, list) else ([error_codes] if error_codes else None),
                        "model_number": meta.get("model_number"),
                        "parent_id": str(meta["parent_id"]) if meta.get("parent_id") else None,
                    },
                )
                inserted_ids.append(chunk_id)
            session.commit()
            logger.info(f"Added {len(texts)} chunks to pgvector for tenant {self.tenant_id}")
            return inserted_ids
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _build_filter_clause(self, metadata_filter: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
        """Build SQL predicate fragments for metadata-aware retrieval."""
        if not metadata_filter:
            return "", {}
        clauses: list[str] = []
        params: dict[str, Any] = {}

        if metadata_filter.get("error_codes"):
            clauses.append("AND error_codes && CAST(:error_codes AS text[])")
            params["error_codes"] = metadata_filter["error_codes"]
        if metadata_filter.get("part_numbers"):
            clauses.append("AND part_numbers && CAST(:part_numbers AS text[])")
            params["part_numbers"] = metadata_filter["part_numbers"]
        if metadata_filter.get("content_type"):
            clauses.append("AND lower(content_type) = lower(:content_type)")
            params["content_type"] = metadata_filter["content_type"]

        return "\n                    ".join(clauses), params

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        session = self._session()
        try:
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
            filter_sql, filter_params = self._build_filter_clause(metadata_filter)
            q = text(f"""
                SELECT id, text, metadata, 1 - (embedding <=> CAST(:embedding AS vector)) AS score
                FROM document_chunks
                WHERE tenant_id = :tenant_id
                    {filter_sql}
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
            """)
            params = {
                "embedding": embedding_str,
                "tenant_id": self.tenant_id,
                "top_k": top_k,
                **filter_params,
            }
            result = session.execute(q, params)
            rows = result.fetchall()
            return [
                SearchResult(
                    text=row.text,
                    score=float(row.score),
                    metadata=dict(row.metadata) if row.metadata else {},
                    document_id=str(row.id),
                )
                for row in rows
            ]
        finally:
            session.close()

    def search_hybrid(
        self,
        query_text: str,
        query_embedding: list[float],
        vector_top_k: int = 40,
        lexical_top_k: int = 40,
        rrf_k: int = 60,
        final_k: int = 20,
        ef_search: int = 80,
        metadata_filter: dict[str, Any] | None = None,
        query_text_alt: str | None = None,
    ) -> list[SearchResult]:
        """Dense + lexical retrieval with RRF fusion. Uses hnsw.ef_search for recall."""
        results, _ = self.search_hybrid_with_debug(
            query_text=query_text,
            query_embedding=query_embedding,
            vector_top_k=vector_top_k,
            lexical_top_k=lexical_top_k,
            rrf_k=rrf_k,
            final_k=final_k,
            ef_search=ef_search,
            metadata_filter=metadata_filter,
            include_debug=False,
            query_text_alt=query_text_alt,
        )
        return results

    def search_hybrid_with_debug(
        self,
        query_text: str,
        query_embedding: list[float],
        vector_top_k: int = 40,
        lexical_top_k: int = 40,
        rrf_k: int = 60,
        final_k: int = 20,
        ef_search: int = 80,
        metadata_filter: dict[str, Any] | None = None,
        include_debug: bool = False,
        query_text_alt: str | None = None,
    ) -> tuple[list[SearchResult], dict[str, Any]]:
        """Dense + lexical retrieval with optional stage-level debug payload.

        query_text_alt: alternative lexical query (e.g. SC200↔SC 200) OR'd
        into the lexical CTEs so FTS is tolerant of hyphen/space variants.
        """
        session = self._session()
        qt_alt = query_text_alt or query_text or " "
        try:
            session.execute(text("SET LOCAL hnsw.ef_search = :v"), {"v": ef_search})
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
            debug_payload: dict[str, Any] = {}
            filter_sql, filter_params = self._build_filter_clause(metadata_filter)

            if include_debug:
                vec_q = text(f"""
                    SELECT id, (1 - (embedding <=> CAST(:embedding AS vector))) AS score
                    FROM document_chunks
                    WHERE tenant_id = CAST(:tenant_id AS uuid)
                    {filter_sql}
                    ORDER BY embedding <=> CAST(:embedding AS vector)
                    LIMIT :vector_top_k
                """)
                vec_rows = session.execute(
                    vec_q,
                    {"embedding": embedding_str, "tenant_id": self.tenant_id, "vector_top_k": vector_top_k, **filter_params},
                ).fetchall()
                debug_payload["vector_hits"] = [
                    {"id": str(r.id), "score": float(r.score or 0)} for r in vec_rows
                ]

                lex_q = text(f"""
                    SELECT id, GREATEST(
                        ts_rank_cd(tsv, websearch_to_tsquery('english', :query_text)),
                        ts_rank_cd(tsv, websearch_to_tsquery('english', :query_text_alt))
                    ) AS score
                    FROM document_chunks
                    WHERE tenant_id = CAST(:tenant_id AS uuid)
                      AND tsv IS NOT NULL
                      AND (tsv @@ websearch_to_tsquery('english', :query_text)
                           OR tsv @@ websearch_to_tsquery('english', :query_text_alt))
                      {filter_sql}
                    ORDER BY score DESC
                    LIMIT :lexical_top_k
                """)
                lex_rows = session.execute(
                    lex_q,
                    {"query_text": query_text or " ", "query_text_alt": qt_alt,
                     "tenant_id": self.tenant_id, "lexical_top_k": lexical_top_k, **filter_params},
                ).fetchall()
                debug_payload["lexical_hits"] = [
                    {"id": str(r.id), "score": float(r.score or 0)} for r in lex_rows
                ]
                debug_payload["lexical_strict_hit_count"] = len(lex_rows)

            q = text(f"""
                WITH vec AS (
                    SELECT id, row_number() OVER (ORDER BY embedding <=> CAST(:embedding AS vector)) AS r_vec
                    FROM document_chunks
                    WHERE tenant_id = CAST(:tenant_id AS uuid)
                    {filter_sql}
                    ORDER BY embedding <=> CAST(:embedding AS vector)
                    LIMIT :vector_top_k
                ),
                lex_strict AS (
                    SELECT id, GREATEST(
                        ts_rank_cd(tsv, websearch_to_tsquery('english', :query_text)),
                        ts_rank_cd(tsv, websearch_to_tsquery('english', :query_text_alt))
                    ) AS score_lex
                    FROM document_chunks
                    WHERE tenant_id = CAST(:tenant_id AS uuid) AND tsv IS NOT NULL
                      AND (tsv @@ websearch_to_tsquery('english', :query_text)
                           OR tsv @@ websearch_to_tsquery('english', :query_text_alt))
                    {filter_sql}
                    ORDER BY score_lex DESC
                    LIMIT :lexical_top_k
                ),
                strict_count AS (SELECT count(*) AS c FROM lex_strict),
                lex_fallback AS (
                    SELECT id, GREATEST(
                        ts_rank_cd(tsv, plainto_tsquery('simple', :query_text)),
                        ts_rank_cd(tsv, plainto_tsquery('simple', :query_text_alt))
                    ) AS score_lex
                    FROM document_chunks
                    WHERE tenant_id = CAST(:tenant_id AS uuid) AND tsv IS NOT NULL
                      AND (tsv @@ plainto_tsquery('simple', :query_text)
                           OR tsv @@ plainto_tsquery('simple', :query_text_alt))
                    {filter_sql}
                    AND (SELECT c FROM strict_count) < 5
                    AND id NOT IN (SELECT id FROM lex_strict)
                    ORDER BY score_lex DESC
                    LIMIT :lexical_top_k
                ),
                lex AS (
                    SELECT id, row_number() OVER (ORDER BY score_lex DESC) AS r_lex
                    FROM (SELECT id, score_lex FROM lex_strict UNION ALL SELECT id, score_lex FROM lex_fallback) u
                ),
                fused AS (
                    SELECT COALESCE(vec.id, lex.id) AS id,
                           (CASE WHEN vec.r_vec IS NULL THEN 0 ELSE 1.0 / (:rrf_k + vec.r_vec) END) +
                           (CASE WHEN lex.r_lex IS NULL THEN 0 ELSE 1.0 / (:rrf_k + lex.r_lex) END) AS rrf
                    FROM vec
                    FULL OUTER JOIN lex ON vec.id = lex.id
                )
                SELECT c.id, c.text, c.metadata, f.rrf AS score
                FROM fused f
                JOIN document_chunks c ON c.id = f.id
                WHERE c.tenant_id = CAST(:tenant_id AS uuid)
                ORDER BY f.rrf DESC
                LIMIT :final_k
            """)
            result = session.execute(
                q,
                {
                    "embedding": embedding_str,
                    "tenant_id": self.tenant_id,
                    "query_text": query_text or " ",
                    "query_text_alt": qt_alt,
                    "vector_top_k": vector_top_k,
                    "lexical_top_k": lexical_top_k,
                    "rrf_k": rrf_k,
                    "final_k": final_k,
                    **filter_params,
                },
            )
            rows = result.fetchall()
            results = [
                SearchResult(
                    text=row.text,
                    score=float(row.score or 0),
                    metadata=dict(row.metadata) if row.metadata else {},
                    document_id=str(row.id),
                )
                for row in rows
            ]
            if include_debug:
                debug_payload["fused_hits_before_rerank"] = [
                    {"id": str(row.id), "score": float(row.score or 0)} for row in rows
                ]
            return results, debug_payload
        finally:
            session.close()

    def delete(self, ids: list[str]) -> None:
        if not ids:
            return
        session = self._session()
        try:
            session.execute(
                text("DELETE FROM document_chunks WHERE id = ANY(:ids) AND tenant_id = :tenant_id"),
                {"ids": ids, "tenant_id": self.tenant_id},
            )
            session.commit()
            logger.info(f"Deleted {len(ids)} chunks from pgvector for tenant {self.tenant_id}")
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def count(self) -> int:
        session = self._session()
        try:
            result = session.execute(
                text("SELECT COUNT(*) FROM document_chunks WHERE tenant_id = :tenant_id"),
                {"tenant_id": self.tenant_id},
            )
            return result.scalar() or 0
        finally:
            session.close()

    def clear(self) -> None:
        session = self._session()
        try:
            session.execute(
                text("DELETE FROM document_chunks WHERE tenant_id = :tenant_id"),
                {"tenant_id": self.tenant_id},
            )
            session.commit()
            logger.info(f"Cleared all chunks for tenant {self.tenant_id}")
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
