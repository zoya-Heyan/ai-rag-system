from fastapi import APIRouter

from app.schemas.common import MessageRequest
from app.services.faiss_store import get_index_stats

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check():
    return {"status": "ok"}


@router.get("/index")
def index_stats():
    """FAISS index status (ready, ntotal)."""
    return get_index_stats()

@router.get("/echo")
def echo(msg: str):
    return {"echo": msg}

@router.post("/echo")
def echo_post(data: MessageRequest):
    return {"echo": data.message}