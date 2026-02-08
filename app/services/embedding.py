from typing import List

from openai import OpenAI

from app.core.config import settings

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def get_embedding(text: str) -> List[float]:
    """Get embedding vector for text. Raises ValueError if API key missing."""
    client = _get_client()
    response = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding