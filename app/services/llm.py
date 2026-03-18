from openai import AsyncOpenAI, OpenAI, RateLimitError

from app.core.config import settings


def _prompt(question: str, context: str) -> str:
    return f"""你是一个严谨的中文 RAG 助手。

你必须严格遵守：
- 只使用【检索上下文】回答；不要引入上下文之外的事实或编造引用。
- 如果上下文不足以回答，直接说“我不知道”，并给出你还需要的补充信息。
- 优先给出结论，其次用要点说明依据；如可能，请在要点中标注来源（文档标题与 chunk 标识）。
- 如果用户问题包含多个子问题，逐条回答。

【检索上下文】
{context}

【用户问题】
{question}
"""


def _get_sync_client() -> OpenAI:
    base_url = settings.LLM_BASE_URL
    api_key = settings.LLM_API_KEY or "EMPTY"
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def _get_async_client() -> AsyncOpenAI:
    base_url = settings.LLM_BASE_URL
    api_key = settings.LLM_API_KEY or "EMPTY"
    if base_url:
        return AsyncOpenAI(api_key=api_key, base_url=base_url)
    return AsyncOpenAI(api_key=api_key)


def ask_llm(question: str, context: str) -> str:
    """Sync LLM call."""
    if not (settings.LLM_API_KEY or settings.LLM_BASE_URL):
        return "LLM not configured. Set LLM_BASE_URL (and optionally LLM_API_KEY)."
    client = _get_sync_client()
    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": _prompt(question, context)},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except RateLimitError:
        return "⚠️ LLM quota exceeded."
    except Exception as e:
        return f"⚠️ LLM error: {str(e)}"


async def ask_llm_async(question: str, context: str) -> str:
    """Async LLM call."""
    if not (settings.LLM_API_KEY or settings.LLM_BASE_URL):
        return "LLM not configured. Set LLM_BASE_URL (and optionally LLM_API_KEY)."
    client = _get_async_client()
    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": _prompt(question, context)},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except RateLimitError:
        return "⚠️ LLM quota exceeded."
    except Exception as e:
        return f"⚠️ LLM error: {str(e)}"
