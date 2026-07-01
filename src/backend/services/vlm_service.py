import base64
import json
import httpx
from pathlib import Path
from backend.config import settings


async def analyze_frame(frame_path: str, camera_id: str, custom_prompt: str | None = None) -> dict:
    """Send a camera frame to the VLM and return structured analysis."""
    image_data = _encode_image(frame_path)

    prompt = custom_prompt or settings.VLM_SYSTEM_PROMPT

    payload = {
        "model": settings.VLM_MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Camera ID: {camera_id}. Analyze this frame."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                ],
            },
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 512,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.VLM_BASE_URL}/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {settings.VLM_API_KEY}"},
        )
        resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"]

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # VLM returned non-JSON; wrap it
        return {
            "incident_detected": False,
            "incident_type": "other",
            "severity": "low",
            "description": content,
            "confidence": 0.0,
        }


def _encode_image(frame_path: str) -> str:
    with open(frame_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
