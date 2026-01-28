from fastapi import FastAPI
from app.routers import health
from app.routers import documents
from app.routers import search

app = FastAPI(title = "AI RAG system")

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(search.router, prefix="/search", tags=["search"])

app.get("/")
def root() :
    return {"message": "Welcome to AI RAG system"}
