from typing import List

from openai import AsyncOpenAI, OpenAI

from app.core.config import settings

_client: OpenAI | None = None
_async_client: AsyncOpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def _get_async_client() -> AsyncOpenAI:
    global _async_client
    if _async_client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        _async_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _async_client


def get_embedding(text: str) -> List[float]:
    """Get embedding vector for text (sync). Raises ValueError if API key missing."""
    client = _get_client()
    response = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


async def get_embedding_async(text: str) -> List[float]:
    """Get embedding vector for text (async). Raises ValueError if API key missing."""
    client = _get_async_client()
    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding