from openai import AsyncOpenAI, OpenAI, RateLimitError

from app.core.config import settings


def _prompt(question: str, context: str) -> str:
    return f"""
You are a helpful AI assistant.
Answer the question using the context below.

Context:
{context}

Question:
{question}
"""


def ask_llm(question: str, context: str) -> str:
    """Sync LLM call."""
    if not settings.OPENAI_API_KEY:
        return "OPENAI_API_KEY not set."
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": _prompt(question, context)}],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except RateLimitError:
        return "⚠️ LLM quota exceeded."
    except Exception as e:
        return f"⚠️ LLM error: {str(e)}"


async def ask_llm_async(question: str, context: str) -> str:
    """Async LLM call."""
    if not settings.OPENAI_API_KEY:
        return "OPENAI_API_KEY not set."
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": _prompt(question, context)}],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except RateLimitError:
        return "⚠️ LLM quota exceeded."
    except Exception as e:
        return f"⚠️ LLM error: {str(e)}"
