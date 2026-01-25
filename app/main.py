from fastapi import FastAPI
from app.routers import health
from app.routers import documents
from app.routers.documents import fake_db
from app.schemas.response import APIResponse

app = FastAPI(title = "AI RAG system")

app.include_router(health.router)
app.include_router(documents.router)

app.get("/")
def root() :
    return {"message": "Welcome to AI RAG system"}
