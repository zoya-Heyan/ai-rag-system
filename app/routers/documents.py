import asyncio
from typing import List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.config import settings
from app.db import (
    get_all_documents,
    get_document_by_id,
    db_create_document,
    update_document,
    delete_document,
    delete_chunks_by_document_id,
    insert_chunks,
)
from app.schemas.response import APIResponse
from app.services.chunking import chunk_text
from app.services.embedding import get_embedding_async
from app.services.index_queue import enqueue_add_chunks, enqueue_rebuild_index

router = APIRouter(prefix="/documents", tags=["documents"])


def _use_postgres(request: Request) -> bool:
    return getattr(request.app.state, "use_postgres", False)


class DocumentSchema(BaseModel):
    id: int
    title: str
    content: str
    embedding: List[float] | None = None


class CreateDocumentSchema(BaseModel):
    title: str
    content: str


class UpdateDocumentSchema(BaseModel):
    title: str | None = None
    content: str | None = None


async def _embed_chunks_concurrent(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts concurrently with rate limit (semaphore)."""
    sem = asyncio.Semaphore(settings.EMBEDDING_CONCURRENCY)

    async def one(text: str):
        async with sem:
            return await get_embedding_async(text)

    return await asyncio.gather(*[one(t) for t in texts])


@router.post("/", response_model=DocumentSchema)
async def create_document(request: Request, body: CreateDocumentSchema):
    chunk_size = settings.CHUNK_SIZE
    overlap = settings.CHUNK_OVERLAP
    chunks_list = chunk_text(body.content, chunk_size=chunk_size, overlap=overlap)
    if not chunks_list:
        chunks_list = [body.content.strip() or body.content]
    try:
        chunk_embeddings = await _embed_chunks_concurrent(chunks_list)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Embedding error: {e}")
    chunk_rows = [(i, chunks_list[i], chunk_embeddings[i]) for i in range(len(chunks_list))]
    if _use_postgres(request):
        from app.db.postgres import create_document_async, insert_chunks_async
        doc = await create_document_async(body.title, body.content, None)
        await insert_chunks_async(doc["id"], chunk_rows)
    else:
        loop = asyncio.get_event_loop()
        executor = request.app.state.executor
        doc = await loop.run_in_executor(
            executor,
            lambda: db_create_document(title=body.title, content=body.content, embedding=None),
        )
        await loop.run_in_executor(executor, lambda: insert_chunks(doc["id"], chunk_rows))
    enqueue_add_chunks(request.app.state.index_queue, doc["id"])
    return DocumentSchema(**doc)


@router.get("/", response_model=APIResponse)
async def list_documents(request: Request):
    if _use_postgres(request):
        from app.db.postgres import get_all_documents_async
        docs = await get_all_documents_async()
    else:
        docs = await asyncio.get_event_loop().run_in_executor(
            request.app.state.executor, get_all_documents
        )
    return APIResponse(success=True, data=docs)


@router.get("/{id}", response_model=DocumentSchema)
async def get_document(request: Request, id: int):
    if _use_postgres(request):
        from app.db.postgres import get_document_by_id_async
        doc = await get_document_by_id_async(id)
    else:
        doc = await asyncio.get_event_loop().run_in_executor(
            request.app.state.executor, lambda: get_document_by_id(id)
        )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentSchema(**doc)


@router.put("/{id}", response_model=DocumentSchema)
async def update_document_route(request: Request, id: int, body: UpdateDocumentSchema):
    if _use_postgres(request):
        from app.db.postgres import (
            get_document_by_id_async,
            update_document_async,
            delete_chunks_by_document_id_async,
            insert_chunks_async,
        )
        doc = await get_document_by_id_async(id)
    else:
        doc = await asyncio.get_event_loop().run_in_executor(
            request.app.state.executor, lambda: get_document_by_id(id)
        )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    updates = {}
    if body.title is not None:
        updates["title"] = body.title
    if body.content is not None:
        updates["content"] = body.content
        chunk_size = settings.CHUNK_SIZE
        overlap = settings.CHUNK_OVERLAP
        chunks_list = chunk_text(body.content, chunk_size=chunk_size, overlap=overlap)
        if not chunks_list:
            chunks_list = [body.content.strip() or body.content]
        try:
            chunk_embeddings = await _embed_chunks_concurrent(chunks_list)
        except ValueError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Embedding error: {e}")
        chunk_rows = [(i, chunks_list[i], chunk_embeddings[i]) for i in range(len(chunks_list))]
        if _use_postgres(request):
            await delete_chunks_by_document_id_async(id)
            await insert_chunks_async(id, chunk_rows)
        else:
            def _replace():
                delete_chunks_by_document_id(id)
                insert_chunks(id, chunk_rows)
            await asyncio.get_event_loop().run_in_executor(
                request.app.state.executor, _replace
            )
        enqueue_rebuild_index(request.app.state.index_queue)
    if not updates:
        return DocumentSchema(**doc)
    if _use_postgres(request):
        updated = await update_document_async(
            id, title=updates.get("title"), content=updates.get("content"), embedding=None
        )
    else:
        updated = await asyncio.get_event_loop().run_in_executor(
            request.app.state.executor,
            lambda: update_document(
                id,
                title=updates.get("title"),
                content=updates.get("content"),
                embedding=None,
            ),
        )
    return DocumentSchema(**updated)


@router.delete("/{id}", status_code=204)
async def delete_document_route(request: Request, id: int):
    if _use_postgres(request):
        from app.db.postgres import delete_document_async
        ok = await delete_document_async(id)
    else:
        ok = await asyncio.get_event_loop().run_in_executor(
            request.app.state.executor, lambda: delete_document(id)
        )
    if not ok:
        raise HTTPException(status_code=404, detail="Document not found")
    enqueue_rebuild_index(request.app.state.index_queue)
