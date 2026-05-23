"""LinkedIn topic research — Google News + Grok.

Pipeline (runs before every scheduled outreach):
1. NewsAPI — fetch the last 3 days of real headlines for the client's field + region
2. Grok — given those headlines as grounding, suggest 5 LinkedIn topics in today's context

This ensures every topic suggestion is anchored to something that actually happened,
not just generic trend guessing.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_GROK_API = "https://api.x.ai/v1/chat/completions"
_NEWS_API = "https://newsapi.org/v2/everything"

_NEWS_PROMPT = (
    "You are a LinkedIn content strategist. Here is what has happened recently in the "
    "{field} field:\n\n"
    "{news_context}\n\n"
    "Also search X/Twitter right now for what professionals in {field} are discussing today.\n\n"
    "The target audience for these posts is: {audience}.\n"
    "The audience is based primarily in: {region}.\n\n"
    "Using the real news above AND current X/Twitter conversation as your source, return "
    "exactly 5 LinkedIn post topic suggestions. Each topic should be timely, grounded in "
    "something real that happened, and written for a thought leader in {field} addressing "
    "{audience} in {region}.\n\n"
    'Return ONLY a JSON array, no markdown:\n'
    '[{{"topic": "...", "angle": "...", "why_today": "..."}}, ...]\n\n'
    "topic = short compelling title, angle = the specific take to argue, "
    "why_today = the real event/news that makes this timely right now."
)

_FALLBACK_PROMPT = (
    "Search X/Twitter and LinkedIn right now for what professionals in {field} are discussing today. "
    "Focus on trends, debates, and opportunities relevant to {audience} in {region}.\n\n"
    "Return exactly 5 LinkedIn post topic suggestions.\n\n"
    'Return ONLY a JSON array, no markdown:\n'
    '[{{"topic": "...", "angle": "...", "why_today": "..."}}, ...]'
)


async def fetch_news_context(field: str, region: str) -> str:
    """Fetch recent headlines from NewsAPI for grounding. Returns empty string on failure."""
    if not settings.news_api_key:
        logger.info("No NEWS_API_KEY — skipping Google News context")
        return ""

    query = field if region in ("Global", "") else f"{field} {region}"
    since = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d")

    try:
        async with httpx.AsyncClient() as http:
            resp = await http.get(
                _NEWS_API,
                params={
                    "q": query,
                    "sortBy": "publishedAt",
                    "pageSize": 8,
                    "language": "en",
                    "from": since,
                },
                headers={"X-Api-Key": settings.news_api_key},
                timeout=10.0,
            )
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            if not articles:
                return ""

            lines = []
            for a in articles[:6]:
                title = a.get("title", "").strip()
                source = a.get("source", {}).get("name", "")
                description = a.get("description", "").strip()
                if title and "[Removed]" not in title:
                    line = f"• {title}"
                    if source:
                        line += f" ({source})"
                    if description:
                        line += f"\n  {description[:120]}"
                    lines.append(line)

            if not lines:
                return ""

            return "Recent news:\n" + "\n".join(lines)

    except Exception:
        logger.exception("NewsAPI fetch failed for field=%r region=%r", field, region)
        return ""


async def fetch_topic_suggestions(
    field: str,
    audience: str = "business professionals",
    region: str = "Global",
) -> list[dict]:
    """Research recent events then use Grok to suggest 5 grounded LinkedIn topics.

    Step 1: NewsAPI pulls real headlines from the last 3 days.
    Step 2: Grok gets those headlines as context + searches X/Twitter live.
    Returns list of dicts with keys: topic, angle, why_today.
    """
    if not settings.grok_api_key:
        logger.info("No GROK_API_KEY — skipping topic suggestions")
        return []

    news_context = await fetch_news_context(field, region)

    if news_context:
        prompt = _NEWS_PROMPT.format(
            field=field,
            audience=audience,
            region=region,
            news_context=news_context,
        )
        logger.info("LinkedIn research: using NewsAPI context (%d chars) for field=%r", len(news_context), field)
    else:
        prompt = _FALLBACK_PROMPT.format(field=field, audience=audience, region=region)
        logger.info("LinkedIn research: no NewsAPI context — Grok-only for field=%r", field)

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
                    "max_tokens": 700,
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
        logger.exception("Grok topic fetch failed for field=%r", field)

    return []
