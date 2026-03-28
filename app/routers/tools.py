"""Study helpers: wrong-question notebook + Markdown notes (RAG-backed optional)."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.llm import chat_async
from app.services.retrieval import retrieve_context

router = APIRouter(prefix="/tools", tags=["tools"])

_WRONG_SYSTEM = """你是学习助手，擅长把零散题目整理成可复习的「错题本」。
输出必须使用 Markdown，结构清晰，语言为简体中文。
不要编造题目中未出现的事实；若信息不足，在「备注」中说明。"""

_NOTES_SYSTEM = """你是笔记助手，根据用户主题与给定资料生成学习笔记。
输出必须是合法的 Markdown：适当使用 #/## 标题、列表、表格、加粗、行内代码与代码块（如需要）。
语言为简体中文。不要编造资料中不存在的内容；资料不足时明确写出「资料未覆盖：…」。"""


class WrongQuestionsRequest(BaseModel):
    raw_text: str = Field(..., min_length=1, max_length=120_000)
    use_knowledge_base: bool = False
    kb_query: str | None = Field(default=None, max_length=4000)
    top_k: int | None = Field(default=5, ge=1, le=16)


class MarkdownNotesRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=8000)
    top_k: int | None = Field(default=6, ge=1, le=16)


@router.post("/wrong-questions")
async def organize_wrong_questions(request: Request, body: WrongQuestionsRequest):
    kb_block = ""
    refs: list[dict] = []
    if body.use_knowledge_base:
        q = (body.kb_query or body.raw_text).strip()[:2000]
        if not q:
            raise HTTPException(status_code=400, detail="知识库检索需要 kb_query 或 raw_text")
        try:
            refs, ctx = await retrieve_context(
                request,
                q,
                body.top_k if body.top_k is not None else settings.SEARCH_TOP_K,
            )
        except ValueError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"检索失败: {e}")
        if ctx.strip():
            kb_block = f"\n\n【知识库检索片段】\n{ctx}\n"

    user_prompt = f"""请把下面材料整理为「错题本」Markdown，建议包含：
- 一级标题：错题整理
- 按题分块：每题含 **题目** / **我的答案**（如有）/ **正确思路或答案** / **错因与要点** / **相关知识点**
若材料中多题混排，请合理分题编号。

【用户粘贴内容】
{body.raw_text}
{kb_block}"""

    text = await chat_async(_WRONG_SYSTEM, user_prompt, temperature=0.25)
    return {"markdown": text, "kb_hits": len(refs), "top_k_results": refs if body.use_knowledge_base else []}


@router.post("/markdown-notes")
async def generate_markdown_notes(request: Request, body: MarkdownNotesRequest):
    try:
        results, context = await retrieve_context(
            request,
            body.topic,
            body.top_k if body.top_k is not None else settings.SEARCH_TOP_K,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"检索失败: {e}")

    if not results:
        user_prompt = f"""主题：{body.topic}

当前知识库中未检索到相关片段。请基于主题生成一份「大纲型」笔记 Markdown（可写应掌握要点清单），并在文首用引用块说明：资料库暂无匹配内容，笔记为通用提纲。"""
    else:
        user_prompt = f"""主题：{body.topic}

【检索到的资料片段】
{context}

请生成结构化的学习笔记（Markdown）。"""

    text = await chat_async(_NOTES_SYSTEM, user_prompt, temperature=0.3)
    return {
        "markdown": text,
        "topic": body.topic,
        "top_k_results": results,
    }
