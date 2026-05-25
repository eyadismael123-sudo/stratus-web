"""Research pipeline for the LinkedIn Post Agent.

Uses Grok API to surface trending content, industry news, and X/Twitter
thought-leader signals relevant to the client's field and audience.
"""

from __future__ import annotations

import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_GROK_API = "https://api.x.ai/v1/chat/completions"


async def fetch_linkedin_signals(
    field: str,
    audience: str,
    topics: list[str],
) -> list[dict]:
    """Use Grok to find what top voices in the client's field are discussing today.

    Returns up to 5 signal dicts: {title, summary, angle, source}.
    angle = the unique take or hook worth writing about.
    """
    if not settings.grok_api_key:
        logger.info("No GROK_API_KEY — skipping LinkedIn signals")
        return []

    focus = ", ".join(topics[:3]) if topics else field
    prompt = (
        f"Search X/Twitter and LinkedIn news right now. "
        f"Find the top 5 things being discussed by professionals in {field}, "
        f"especially around: {focus}. "
        f"Target audience for LinkedIn posts: {audience}. "
        f"For each signal, identify a specific angle or contrarian take that would "
        f"resonate with {audience}. "
        f"Return as a JSON array. Each item: "
        f'{{\"title\": \"...\", \"summary\": \"...\", \"angle\": \"...\", \"source\": \"...\"}}. '
        f"No markdown. Only the JSON array."
    )

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _GROK_API,
                headers={
                    "Authorization": f"Bearer {settings.grok_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "grok-3",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.4,
                },
                timeout=25.0,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()

            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])

    except Exception:
        logger.exception("Grok LinkedIn research failed for field=%s", field)

    return []
