from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.db import get_all_documents
from app.services.embedding import get_embedding
from app.services.llm import ask_llm
from app.services.similarity import cosine_similarity

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    use_llm: bool = True  # 是否用 LLM 基于检索结果生成回答


@router.post("/")
def search_documents(request: QueryRequest):
    try:
        query_embedding = get_embedding(request.query)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Embedding error: {e}")

    docs = get_all_documents()
    scored_docs = []
    for doc in docs:
        if not doc.get("embedding"):
            continue
        score = cosine_similarity(query_embedding, doc["embedding"])
        scored_docs.append((doc, score))

    scored_docs = sorted(scored_docs, key=lambda x: x[1], reverse=True)
    top_k = settings.SEARCH_TOP_K
    top_docs = scored_docs[:top_k]

    results = []
    for doc, score in top_docs:
        content = doc["content"]
        results.append({
            "id": doc["id"],
            "title": doc["title"],
            "content": content,
            "content_preview": content[:100] + ("..." if len(content) > 100 else ""),
            "score": round(score, 4),
        })

    answer = None
    if results and request.use_llm:
        context = "\n\n---\n\n".join(f"[{d['title']}]\n{d['content']}" for d, _ in top_docs)
        answer = ask_llm(request.query, context)
    elif not results:
        answer = "no relevant documents"

    return {
        "question": request.query,
        "top_k_results": results,
        "answer": answer,
    }