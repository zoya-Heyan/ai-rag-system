from fastapi import APIRouter
from app.schemas.common import MessageRequest

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check():
    return {"status": "ok"}

@router.get("/echo")
def echo(msg: str):
    return {"echo": msg}

@router.post("/echo")
def echo_post(data: MessageRequest):
    return {"echo": data.message}