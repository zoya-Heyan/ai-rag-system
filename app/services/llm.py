from openai import OpenAI, RateLimitError

from app.core.config import settings


def ask_llm(question: str, context: str) -> str:
    if not settings.OPENAI_API_KEY:
        return "OPENAI_API_KEY not set."

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = f"""
You are a helpful AI assistant.
Answer the question using the context below.

Context:
{context}

Question:
{question}
"""

    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content

    except RateLimitError:
        return "⚠️ LLM quota exceeded."

    except Exception as e:
        return f"⚠️ LLM error: {str(e)}"
