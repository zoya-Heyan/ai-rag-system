"""Sync PostgreSQL access for index worker (same process, no async)."""
import json
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings


def _get_conn():
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg2.connect(settings.DATABASE_URL, cursor_factory=RealDictCursor)


def get_all_chunks_with_document_info() -> list[dict[str, Any]]:
    """Same contract as database.get_all_chunks_with_document_info for index build."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.document_id, c.chunk_index, c.content, c.embedding,
                       d.title AS document_title
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                ORDER BY c.document_id, c.chunk_index
            """)
            rows = cur.fetchall()
            return [_row_to_chunk(dict(r)) for r in rows]
    finally:
        conn.close()


def get_chunks_by_document_id(doc_id: int) -> list[dict[str, Any]]:
    """Same contract as database.get_chunks_by_document_id for incremental add."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.document_id, c.chunk_index, c.content, c.embedding,
                       d.title AS document_title
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.document_id = %s
                ORDER BY c.chunk_index
            """, (doc_id,))
            rows = cur.fetchall()
            return [_row_to_chunk(dict(r)) for r in rows]
    finally:
        conn.close()


def _row_to_chunk(d: dict) -> dict[str, Any]:
    if d.get("embedding") is not None and isinstance(d["embedding"], str):
        d["embedding"] = json.loads(d["embedding"])
    return d
