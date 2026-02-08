from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import (
    get_all_documents,
    get_document_by_id,
    db_create_document,
    update_document,
    delete_document,
)
from app.schemas.response import APIResponse
from app.services.embedding import get_embedding

router = APIRouter(prefix="/documents", tags=["documents"])


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


@router.post("/", response_model=DocumentSchema)
def create_document(body: CreateDocumentSchema):
    try:
        embedding = get_embedding(body.content)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Embedding error: {e}")
    doc = db_create_document(title=body.title, content=body.content, embedding=embedding)
    return DocumentSchema(**doc)


@router.get("/", response_model=APIResponse)
def list_documents():
    docs = get_all_documents()
    return APIResponse(success=True, data=docs)


@router.get("/{id}", response_model=DocumentSchema)
def get_document(id: int):
    doc = get_document_by_id(id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentSchema(**doc)


@router.put("/{id}", response_model=DocumentSchema)
def update_document_route(id: int, body: UpdateDocumentSchema):
    doc = get_document_by_id(id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    updates = {}
    if body.title is not None:
        updates["title"] = body.title
    if body.content is not None:
        updates["content"] = body.content
        try:
            updates["embedding"] = get_embedding(body.content)
        except ValueError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Embedding error: {e}")
    if not updates:
        return DocumentSchema(**doc)
    updated = update_document(
        id,
        title=updates.get("title"),
        content=updates.get("content"),
        embedding=updates.get("embedding"),
    )
    return DocumentSchema(**updated)


@router.delete("/{id}", status_code=204)
def delete_document_route(id: int):
    if not delete_document(id):
        raise HTTPException(status_code=404, detail="Document not found")
