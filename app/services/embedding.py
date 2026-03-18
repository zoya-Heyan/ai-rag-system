import asyncio
import threading
from typing import List

from sentence_transformers import SentenceTransformer

from app.core.config import settings

_lock = threading.Lock()
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is not None:
        return _model
    with _lock:
        if _model is None:
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return _model


def _embed_sync(text: str) -> List[float]:
    model = _get_model()
    vec = model.encode(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return vec.astype("float32").tolist()


def get_embedding(text: str) -> List[float]:
    """Get embedding vector for text (sync, local sentence-transformers)."""
    if not text:
        return _embed_sync("")
    return _embed_sync(text)


async def get_embedding_async(text: str) -> List[float]:
    """Get embedding vector for text (async, runs in a worker thread)."""
    return await asyncio.to_thread(get_embedding, text)