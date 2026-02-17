import os
from typing import Optional


class Settings:
    """Application settings from environment."""

    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")  # e.g. postgresql://user:pass@host:5432/dbname
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    SEARCH_TOP_K: int = int(os.getenv("SEARCH_TOP_K", "5"))

    # Chunking
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))

    # Embeddings
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "1536"))  # text-embedding-3-small
    EMBEDDING_CONCURRENCY: int = int(os.getenv("EMBEDDING_CONCURRENCY", "5"))  # max concurrent embedding calls

    # FAISS IVF parameters
    FAISS_NLIST: int = int(os.getenv("FAISS_NLIST", "100"))   # number of inverted lists
    FAISS_NPROBE: int = int(os.getenv("FAISS_NPROBE", "10"))  # how many lists to search
    FAISS_MIN_TRAIN: int = int(os.getenv("FAISS_MIN_TRAIN", "1000"))  # below this fallback to Flat


settings = Settings()
