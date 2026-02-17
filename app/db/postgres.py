"""PostgreSQL async persistence (when DATABASE_URL is set)."""
from typing import Any

import asyncpg

from app.core.config import settings

_pool: asyncpg.Pool | None = None


async def init_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        if not settings.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set")
        _pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=60,
        )
    return _pool


def get_pool() -> asyncpg.Pool | None:
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def init_db_async() -> None:
    pool = await init_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding JSONB
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding JSONB NOT NULL
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)"
        )


def _row_to_doc(row: asyncpg.Record) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "content": row["content"],
        "embedding": row["embedding"],
    }


def _row_to_chunk(row: asyncpg.Record) -> dict[str, Any]:
    return {
        "id": row["id"],
        "document_id": row["document_id"],
        "chunk_index": row["chunk_index"],
        "content": row["content"],
        "embedding": row["embedding"],
        "document_title": row["document_title"],
    }


async def get_all_documents_async() -> list[dict[str, Any]]:
    pool = get_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, title, content, embedding FROM documents ORDER BY id"
        )
        return [_row_to_doc(r) for r in rows]


async def get_document_by_id_async(doc_id: int) -> dict[str, Any] | None:
    pool = get_pool()
    if not pool:
        return None
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, title, content, embedding FROM documents WHERE id = $1",
            doc_id,
        )
        return _row_to_doc(row) if row else None


async def create_document_async(
    title: str, content: str, embedding: list[float] | None
) -> dict[str, Any]:
    pool = get_pool()
    if not pool:
        raise RuntimeError("Postgres pool not initialized")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO documents (title, content, embedding)
            VALUES ($1, $2, $3)
            RETURNING id, title, content, embedding
            """,
            title,
            content,
            embedding,
        )
        return _row_to_doc(row)


async def update_document_async(
    doc_id: int,
    *,
    title: str | None = None,
    content: str | None = None,
    embedding: list[float] | None = None,
) -> dict[str, Any] | None:
    doc = await get_document_by_id_async(doc_id)
    if not doc:
        return None
    updates = []
    values: list[Any] = []
    if title is not None:
        values.append(title)
        updates.append(f"title = ${len(values)}")
    if content is not None:
        values.append(content)
        updates.append(f"content = ${len(values)}")
    if embedding is not None:
        values.append(embedding)
        updates.append(f"embedding = ${len(values)}")
    if not updates:
        return doc
    values.append(doc_id)
    pool = get_pool()
    if not pool:
        return None
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE documents SET {', '.join(updates)} WHERE id = ${len(values)}",
            *values,
        )
    return await get_document_by_id_async(doc_id)


async def delete_document_async(doc_id: int) -> bool:
    pool = get_pool()
    if not pool:
        return False
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM documents WHERE id = $1",
            doc_id,
        )
        return result == "DELETE 1"


async def delete_chunks_by_document_id_async(doc_id: int) -> None:
    pool = get_pool()
    if not pool:
        return
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM chunks WHERE document_id = $1", doc_id)


async def insert_chunks_async(
    document_id: int, chunks: list[tuple[int, str, list[float]]]
) -> None:
    if not chunks:
        return
    pool = get_pool()
    if not pool:
        raise RuntimeError("Postgres pool not initialized")
    async with pool.acquire() as conn:
        for chunk_index, content, embedding in chunks:
            await conn.execute(
                """
                INSERT INTO chunks (document_id, chunk_index, content, embedding)
                VALUES ($1, $2, $3, $4)
                """,
                document_id,
                chunk_index,
                content,
                embedding,
            )


async def get_all_chunks_with_document_info_async() -> list[dict[str, Any]]:
    pool = get_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.id, c.document_id, c.chunk_index, c.content, c.embedding,
                   d.title AS document_title
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            ORDER BY c.document_id, c.chunk_index
        """)
        return [_row_to_chunk(r) for r in rows]


async def get_chunks_by_document_id_async(doc_id: int) -> list[dict[str, Any]]:
    pool = get_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.id, c.document_id, c.chunk_index, c.content, c.embedding,
                   d.title AS document_title
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.document_id = $1
            ORDER BY c.chunk_index
        """, doc_id)
        return [_row_to_chunk(r) for r in rows]
