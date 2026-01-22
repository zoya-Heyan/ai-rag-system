from fastapi import FastAPI

app = FastAPI(title = "AI RAG system")

app.get("/")
def root() :
    return {"message": "Welcome to AI RAG system"}

@app.get("/health")
def health() :
    return {"status": "OK"}
