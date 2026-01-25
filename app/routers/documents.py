from app.schemas.response import APIResponse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix = "/documents", tags = ["documents"])

fake_db = []

class DocumentSchema(BaseModel) :
    id : int
    title : str
    content : str

@router.post("/", response_model=DocumentSchema)
def create_document(doc: DocumentSchema):
    fake_db.append(doc)
    return doc

@router.get("/", response_model=List[DocumentSchema])
def list_documents():
    return fake_db

@router.get("/{id}", response_model=DocumentSchema)
def get_document(id: int):
    for doc in fake_db :
        if doc.id == id:
            return doc
    raise HTTPException(status_code=404, detail="Document not found")


@router.get("/", response_model=APIResponse)
def list_documents() :
    return APIResponse(success=True, data=fake_db)