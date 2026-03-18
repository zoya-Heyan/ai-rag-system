import os
from typing import Optional


class Settings:
    """Application settings from environment."""

    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")  # e.g. postgresql://user:pass@host:5432/dbname
    # LLM (Qwen 7B by default). Uses OpenAI-compatible Chat Completions API.
    # Compatible backends: DashScope OpenAI-compatible endpoint / vLLM / LiteLLM / etc.
    LLM_BASE_URL = "http://localhost:11434/v1" # e.g. http://localhost:8001/v1
    LLM_MODEL = "qwen:7b"
    LLM_API_KEY = "ollama"

    # Embeddings (local sentence-transformers)
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")

    SEARCH_TOP_K: int = int(os.getenv("SEARCH_TOP_K", "3"))

    # Chunking
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "400"))  # recommended 300~500
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))

    # Embeddings
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "512"))  # bge-small-zh-v1.5
    EMBEDDING_CONCURRENCY: int = int(os.getenv("EMBEDDING_CONCURRENCY", "4"))  # local CPU, keep modest

    # FAISS IVF parameters
    FAISS_NLIST: int = int(os.getenv("FAISS_NLIST", "100"))   # number of inverted lists
    FAISS_NPROBE: int = int(os.getenv("FAISS_NPROBE", "10"))  # how many lists to search
    FAISS_MIN_TRAIN: int = int(os.getenv("FAISS_MIN_TRAIN", "1000"))  # below this fallback to Flat


settings = Settings()
