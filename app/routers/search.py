from fastapi import APIRouter
from pydantic import BaseModel
from app.services.embedding import get_embedding
from app.services.llm import ask_llm
from app.services.similarity import cosine_similarity
from app.routers.documents import fake_db, DocumentSchema

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/")
def search_documents(request: QueryRequest):
    query_embedding = get_embedding(request.query)

    best_score = -1
    best_doc = None

    for doc in fake_db:
        if not doc.embedding:
            continue
        score = cosine_similarity(query_embedding, doc.embedding)
        if score > best_score:
            best_score = score
            best_doc = doc

    if not best_doc:
        return {"answer": "No relevant documents found."}

    answer = ask_llm(request.query, best_doc.content)

    return {
        "question": request.query,
        "matched_document": best_doc.title,
        "similarity_score": best_score,
        "answer": answer
    }