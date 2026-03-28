import asyncio

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.llm import ask_llm_async
from app.services.retrieval import retrieve_context

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    use_llm: bool = True  # 是否用 LLM 基于检索结果生成回答
    top_k: int | None = Field(default=None, ge=1, le=32)  # 覆盖默认 SEARCH_TOP_K


@router.post("/")
async def search_documents(request: Request, request_body: QueryRequest):
    try:
        results, context = await retrieve_context(
            request,
            request_body.query,
            request_body.top_k if request_body.top_k is not None else settings.SEARCH_TOP_K,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Embedding error: {e}")

    answer = None
    if results and request_body.use_llm:
        answer = await ask_llm_async(request_body.query, context)
    elif not results:
        answer = "no relevant documents"

    return {
        "question": request_body.query,
        "top_k_results": results,
        "answer": answer,
    }
