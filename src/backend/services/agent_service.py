import httpx
from backend.config import settings

AGENT_SYSTEM_PROMPT = """You are a city traffic surveillance assistant with access to a database of camera incidents.
You help operators query incidents, generate reports, and understand traffic patterns.
When answering, be concise and factual. If asked for a report, structure it clearly.
Today's context will be provided as JSON in the user message."""


async def query_agent(question: str, context: dict) -> str:
    """Send a natural language query + DB context to the LLM agent."""
    context_text = _format_context(context)

    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {question}"},
        ],
        "max_tokens": 1024,
        "temperature": 0.3,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.LLM_BASE_URL}/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
        )
        resp.raise_for_status()

    return resp.json()["choices"][0]["message"]["content"]


def _format_context(context: dict) -> str:
    import json
    return json.dumps(context, indent=2, default=str)
