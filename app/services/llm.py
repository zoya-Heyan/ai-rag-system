import os
from openai import OpenAI
from openai import RateLimitError

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_llm(question: str, context: str) -> str:
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
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content

    except RateLimitError:
        return "⚠️ LLM quota exceeded. Please check API billing."

    except Exception as e:
        return f"⚠️ LLM error: {str(e)}"
