"""LinkedIn topic research via Grok API.

Scans X/Twitter for what professionals in the client's industry are
discussing today and suggests 5 post topics.
"""

from __future__ import annotations

import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_GROK_API = "https://api.x.ai/v1/chat/completions"

_PROMPT = (
    "Search X/Twitter and LinkedIn right now for what professionals in the {field} "
    "field are discussing today. Focus on: trends, debates, insights, and opportunities.\n\n"
    "The target audience for these posts is: {audience}.\n"
    "The audience is based primarily in: {region}.\n\n"
    "Return exactly 5 topic suggestions for a LinkedIn post. Each topic should be timely, "
    "relevant, and something a thought leader in {field} writing for {audience} in {region} "
    "would want to publish today.\n\n"
    'Return ONLY a JSON array, no markdown:\n'
    '[{{"topic": "...", "angle": "...", "why_today": "..."}}, ...]\n\n'
    "Fields: topic = short title, angle = suggested take, why_today = relevance right now."
)


async def fetch_topic_suggestions(
    field: str,
    audience: str = "business professionals",
    region: str = "Global",
) -> list[dict]:
    """Use Grok to suggest 5 LinkedIn post topics based on current trends.

    Returns list of dicts with keys: topic, angle, why_today.
    Returns empty list when Grok is unavailable.
    """
    if not settings.grok_api_key:
        logger.info("No GROK_API_KEY — skipping topic suggestions")
        return []

    prompt = _PROMPT.format(field=field, audience=audience, region=region)

    try:
        async with httpx.AsyncClient() as http:
            resp = await http.post(
                _GROK_API,
                headers={
                    "Authorization": f"Bearer {settings.grok_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "grok-3",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 600,
                    "temperature": 0.4,
                },
                timeout=20.0,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()

            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])

    except Exception:
        logger.exception("Grok topic fetch failed for field=%r", field)

    return []
