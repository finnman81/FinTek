"""
Validate that full-text search (lexical) is functional on document_chunks.

Run diagnostic queries suggested for 91% lexical-zero-hit rate:
- Count matches using on-the-fly to_tsvector('english', text)
- Count matches using stored tsv column (what the app uses)
- Total chunks and tsv population

Usage: python scripts/validate_lexical_fts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from src.db.connection import get_session_factory


def main() -> None:
    session_factory = get_session_factory()
    session = session_factory()
    try:
        # 1) Total chunks
        total = session.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar()
        print(f"Total document_chunks: {total}")

        # 2) Chunks with non-null tsv (stored tsvector)
        tsv_populated = session.execute(
            text("SELECT COUNT(*) FROM document_chunks WHERE tsv IS NOT NULL")
        ).scalar()
        print(f"Chunks with tsv IS NOT NULL: {tsv_populated}")

        # 3) User's exact diagnostic: on-the-fly to_tsvector('english', text)
        q1 = "installation procedure"
        count_on_the_fly = session.execute(
            text("""
                SELECT COUNT(*) FROM document_chunks
                WHERE to_tsvector('english', text) @@ websearch_to_tsquery('english', :q)
            """),
            {"q": q1},
        ).scalar()
        print(f"\n[On-the-fly to_tsvector('english', text)]")
        print(f"  websearch_to_tsquery('english', {q1!r}) => COUNT = {count_on_the_fly}")

        # 4) Stored tsv column (what the app actually uses)
        count_stored = session.execute(
            text("""
                SELECT COUNT(*) FROM document_chunks
                WHERE tsv IS NOT NULL AND tsv @@ websearch_to_tsquery('english', :q)
            """),
            {"q": q1},
        ).scalar()
        print(f"\n[Stored tsv column]")
        print(f"  websearch_to_tsquery('english', {q1!r}) => COUNT = {count_stored}")

        # 5) A few more real-looking queries
        for q in [
            "installation procedure",
            "Fleck 9000",
            "replace valve",
            "part number",
            "error code",
            "safety warning",
        ]:
            c = session.execute(
                text("""
                    SELECT COUNT(*) FROM document_chunks
                    WHERE tsv IS NOT NULL AND tsv @@ websearch_to_tsquery('english', :q)
                """),
                {"q": q},
            ).scalar()
            print(f"  websearch_to_tsquery('english', {q!r}) => {c}")

        # 6) plainto_tsquery('simple', ...) for same queries (fallback config)
        print("\n[Stored tsv + plainto_tsquery('simple', q)]")
        for q in ["installation procedure", "Fleck 9000", "replace valve"]:
            c = session.execute(
                text("""
                    SELECT COUNT(*) FROM document_chunks
                    WHERE tsv IS NOT NULL AND tsv @@ plainto_tsquery('simple', :q)
                """),
                {"q": q},
            ).scalar()
            print(f"  plainto_tsquery('simple', {q!r}) => {c}")

    finally:
        session.close()


if __name__ == "__main__":
    main()
