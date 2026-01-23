from fastapi import FastAPI
from app.routers import health

app = FastAPI(title = "AI RAG system")

app.include_router(health.router)

app.get("/")
def root() :
    return {"message": "Welcome to AI RAG system"}
