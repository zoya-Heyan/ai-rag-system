"""SQLite persistence for documents."""
import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "rag.db"


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create documents and chunks tables if not exists."""
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)")
        conn.commit()
    finally:
        conn.close()


def _row_to_doc(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    if d.get("embedding"):
        d["embedding"] = json.loads(d["embedding"])
    else:
        d["embedding"] = None
    return d


def get_all_documents() -> list[dict[str, Any]]:
    """Return all documents with embedding decoded."""
    conn = _get_connection()
    try:
        cur = conn.execute("SELECT id, title, content, embedding FROM documents ORDER BY id")
        return [_row_to_doc(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_document_by_id(doc_id: int) -> dict[str, Any] | None:
    """Return one document by id or None."""
    conn = _get_connection()
    try:
        cur = conn.execute(
            "SELECT id, title, content, embedding FROM documents WHERE id = ?",
            (doc_id,),
        )
        row = cur.fetchone()
        return _row_to_doc(row) if row else None
    finally:
        conn.close()


def create_document(title: str, content: str, embedding: list[float] | None) -> dict[str, Any]:
    """Insert document and return it with assigned id."""
    conn = _get_connection()
    try:
        emb_json = json.dumps(embedding) if embedding else None
        cur = conn.execute(
            "INSERT INTO documents (title, content, embedding) VALUES (?, ?, ?)",
            (title, content, emb_json),
        )
        conn.commit()
        doc_id = cur.lastrowid
        return {"id": doc_id, "title": title, "content": content, "embedding": embedding}
    finally:
        conn.close()


def update_document(
    doc_id: int,
    *,
    title: str | None = None,
    content: str | None = None,
    embedding: list[float] | None = None,
) -> dict[str, Any] | None:
    """Update document by id. None means leave field unchanged. Returns updated doc or None."""
    doc = get_document_by_id(doc_id)
    if not doc:
        return None
    updates = []
    params: list[Any] = []
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if content is not None:
        updates.append("content = ?")
        params.append(content)
    if embedding is not None:
        updates.append("embedding = ?")
        params.append(json.dumps(embedding))
    if not updates:
        return doc
    params.append(doc_id)
    conn = _get_connection()
    try:
        conn.execute(
            f"UPDATE documents SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()
        return get_document_by_id(doc_id)
    finally:
        conn.close()


def delete_document(doc_id: int) -> bool:
    """Delete document by id (and its chunks via CASCADE or explicit delete). Returns True if deleted."""
    conn = _get_connection()
    try:
        conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
        cur = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_chunks_by_document_id(doc_id: int) -> None:
    """Remove all chunks for a document (e.g. before re-chunking on update)."""
    conn = _get_connection()
    try:
        conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
        conn.commit()
    finally:
        conn.close()


def insert_chunks(document_id: int, chunks: list[tuple[int, str, list[float]]]) -> None:
    """Insert chunks for a document. Each item is (chunk_index, content, embedding)."""
    if not chunks:
        return
    conn = _get_connection()
    try:
        for chunk_index, content, embedding in chunks:
            conn.execute(
                "INSERT INTO chunks (document_id, chunk_index, content, embedding) VALUES (?, ?, ?, ?)",
                (document_id, chunk_index, content, json.dumps(embedding)),
            )
        conn.commit()
    finally:
        conn.close()


def _row_to_chunk(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    if d.get("embedding"):
        d["embedding"] = json.loads(d["embedding"])
    return d


def get_all_chunks_with_document_info() -> list[dict[str, Any]]:
    """Return all chunks with document_id and document title for retrieval."""
    conn = _get_connection()
    try:
        cur = conn.execute("""
            SELECT c.id, c.document_id, c.chunk_index, c.content, c.embedding, d.title AS document_title
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            ORDER BY c.document_id, c.chunk_index
        """)
        return [_row_to_chunk(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_chunks_by_document_id(doc_id: int) -> list[dict[str, Any]]:
    """Return chunks for one document (with embedding) for incremental index add."""
    conn = _get_connection()
    try:
        cur = conn.execute("""
            SELECT c.id, c.document_id, c.chunk_index, c.content, c.embedding, d.title AS document_title
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.document_id = ?
            ORDER BY c.chunk_index
        """, (doc_id,))
        return [_row_to_chunk(r) for r in cur.fetchall()]
    finally:
        conn.close()
