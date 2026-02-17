"""Split text into overlapping chunks for RAG."""


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split text into chunks of at most chunk_size characters, with overlap between
    consecutive chunks. overlap must be < chunk_size.
    """
    if not text or not text.strip():
        return []
    if chunk_size <= 0:
        return [text.strip()] if text.strip() else []
    overlap = min(max(0, overlap), chunk_size - 1)
    step = chunk_size - overlap
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += step
    return chunks
