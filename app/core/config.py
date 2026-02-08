import os
from typing import Optional


class Settings:
    """Application settings from environment."""

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    SEARCH_TOP_K: int = int(os.getenv("SEARCH_TOP_K", "5"))


settings = Settings()
