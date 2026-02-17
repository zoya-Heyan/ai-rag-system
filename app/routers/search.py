import asyncio

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.config import settings
from app.db import get_all_chunks_with_document_info, get_all_documents
from app.services.embedding import get_embedding_async
from app.services.faiss_store import ensure_index, search as faiss_search
from app.services.llm import ask_llm_async
from app.services.similarity import cosine_similarity

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    use_llm: bool = True  # 是否用 LLM 基于检索结果生成回答


def _search_by_chunks(
    query_embedding: list[float], top_k: int, chunks: list[dict]
):
    """Retrieve top_k chunks by similarity. Returns (results list, top_chunks for LLM)."""
    scored = [(ch, cosine_similarity(query_embedding, ch["embedding"])) for ch in chunks if ch.get("embedding")]
    scored.sort(key=lambda x: x[1], reverse=True)
    top_chunks = scored[:top_k]
    results = []
    for ch, score in top_chunks:
        content = ch["content"]
        results.append({
            "chunk_id": ch["id"],
            "document_id": ch["document_id"],
            "document_title": ch["document_title"],
            "chunk_index": ch["chunk_index"],
            "content": content,
            "content_preview": content[:100] + ("..." if len(content) > 100 else ""),
            "score": round(score, 4),
        })
    return results, top_chunks


def _search_by_documents(
    query_embedding: list[float], top_k: int, docs: list[dict]
):
    """Fallback: document-level search (no chunks). Returns (results list, top_docs for LLM)."""
    scored = [(d, cosine_similarity(query_embedding, d["embedding"])) for d in docs if d.get("embedding")]
    scored.sort(key=lambda x: x[1], reverse=True)
    top_docs = scored[:top_k]
    results = []
    for doc, score in top_docs:
        content = doc["content"]
        results.append({
            "document_id": doc["id"],
            "document_title": doc["title"],
            "content": content,
            "content_preview": content[:100] + ("..." if len(content) > 100 else ""),
            "score": round(score, 4),
        })
    return results, top_docs


def _use_postgres(request: Request) -> bool:
    return getattr(request.app.state, "use_postgres", False)


@router.post("/")
async def search_documents(request: Request, request_body: QueryRequest):
    try:
        query_embedding = await get_embedding_async(request_body.query)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Embedding error: {e}")

    top_k = settings.SEARCH_TOP_K
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(request.app.state.executor, ensure_index)
    faiss_results = faiss_search(query_embedding, top_k)
    if faiss_results:
        results = []
        for info, score in faiss_results:
            content = info["content"]
            results.append({
                "chunk_id": info["chunk_id"],
                "document_id": info["document_id"],
                "document_title": info["document_title"],
                "chunk_index": info["chunk_index"],
                "content": content,
                "content_preview": content[:100] + ("..." if len(content) > 100 else ""),
                "score": round(score, 4),
            })
        context_blocks = [
            f"[{info['document_title']} (chunk {info['chunk_index']})]\n{info['content']}"
            for info, _ in faiss_results
        ]
    else:
        if _use_postgres(request):
            from app.db.postgres import (
                get_all_chunks_with_document_info_async,
                get_all_documents_async,
            )
            chunks = await get_all_chunks_with_document_info_async()
            docs = await get_all_documents_async()
        else:
            chunks = await loop.run_in_executor(
                request.app.state.executor, get_all_chunks_with_document_info
            )
            docs = await loop.run_in_executor(
                request.app.state.executor, get_all_documents
            )
        if chunks:
            results, top_items = _search_by_chunks(query_embedding, top_k, chunks)
            context_blocks = [
                f"[{ch['document_title']} (chunk {ch['chunk_index']})]\n{ch['content']}"
                for ch, _ in top_items
            ]
        else:
            results, top_items = _search_by_documents(query_embedding, top_k, docs)
            context_blocks = [f"[{d['title']}]\n{d['content']}" for d, _ in top_items]

    answer = None
    if results and request_body.use_llm:
        context = "\n\n---\n\n".join(context_blocks)
        answer = await ask_llm_async(request_body.query, context)
    elif not results:
        answer = "no relevant documents"

    return {
        "question": request_body.query,
        "top_k_results": results,
        "answer": answer,
    }