"""Research pipeline for the LinkedIn Post Agent.

Uses Grok API to surface trending content, industry news, and X/Twitter
thought-leader signals relevant to the client's field and audience.
"""

from __future__ import annotations

import asyncio
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
    """Use Grok to find trending signals + hashtags for the client's field.

    Returns up to 5 signal dicts: {title, summary, angle, source, hashtags}.
    """
    if not settings.grok_api_key:
        logger.info("No GROK_API_KEY — skipping LinkedIn signals")
        return []

    focus = ", ".join(topics[:3]) if topics else field
    prompt = (
        f"Search X/Twitter and LinkedIn right now. "
        f"Find the top 5 things being discussed by professionals in {field}, "
        f"especially around: {focus}. "
        f"Target audience: {audience}. "
        f"For each signal, identify a specific angle or contrarian take that would resonate. "
        f"Also suggest 2-3 LinkedIn hashtags per signal (mix of popular and niche). "
        f"Return as a JSON array. Each item: "
        f'{{\"title\": \"...\", \"summary\": \"...\", \"angle\": \"...\", '
        f'\"source\": \"...\", \"hashtags\": [\"#Tag1\", \"#Tag2\"]}}. '
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
                    "max_tokens": 1200,
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


async def fetch_web_signals(
    field: str,
    audience: str,
    topics: list[str],
) -> list[dict]:
    """DuckDuckGo news search for recent articles relevant to the client's field.

    Returns up to 5 signal dicts: {title, summary, angle, source, hashtags}.
    No API key required.
    """
    try:
        from duckduckgo_search import DDGS

        focus = ", ".join(topics[:2]) if topics else field
        query = f"{field} {focus} professionals news 2025"

        results = await asyncio.to_thread(
            lambda: list(DDGS().news(query, max_results=5))
        )

        signals = []
        for r in results:
            title = r.get("title", "")
            body = r.get("body", "") or r.get("excerpt", "")
            source = r.get("source", "") or r.get("url", "")
            signals.append({
                "title": title,
                "summary": body[:300] if body else title,
                "angle": f"What {audience} should know about: {title}",
                "source": source,
                "hashtags": [f"#{field.replace(' ', '')}", f"#{audience.replace(' ', '')}", "#LinkedIn"],
            })
        return signals

    except Exception:
        logger.exception("DuckDuckGo web search failed for field=%s", field)
        return []


async def fetch_all_signals(
    field: str,
    audience: str,
    topics: list[str],
) -> list[dict]:
    """Run Grok + DuckDuckGo in parallel and return merged, deduplicated signals."""
    grok_signals, web_signals = await asyncio.gather(
        fetch_linkedin_signals(field, audience, topics),
        fetch_web_signals(field, audience, topics),
    )

    seen_titles: set[str] = set()
    merged: list[dict] = []
    for s in grok_signals + web_signals:
        title = s.get("title", "").lower()[:60]
        if title not in seen_titles:
            seen_titles.add(title)
            merged.append(s)

    return merged[:8]


async def generate_angles_from_signals(
    signals: list[dict],
    memory: dict,
) -> list[dict]:
    """Use Claude Haiku to turn Grok signals into 3 crisp post angles for the client.

    Returns list of {hook, angle, signal_index, hashtags}.
    hook = first line only, punchy enough to show in a button.
    """
    from anthropic import Anthropic
    from app.config import settings

    if not signals or not settings.anthropic_api_key:
        return []

    field = memory.get("field", "")
    voice_tone = memory.get("voice_tone", "professional")
    topics = memory.get("topics", [])

    signals_text = "\n".join(
        f"{i+1}. {s.get('title', '')} — {s.get('angle', '')} | hashtags: {', '.join(s.get('hashtags', []))}"
        for i, s in enumerate(signals[:5])
    )

    prompt = f"""You are a LinkedIn ghostwriter for a {field} professional.
Their voice: {voice_tone}
Their topics: {', '.join(topics)}

Here are today's research signals:
{signals_text}

Pick the 3 most compelling angles for a LinkedIn post. For each:
- Write a punchy hook (first line only, max 12 words, no "I" as first word)
- State the angle in one sentence
- Note which signal index (1-5) it draws from
- List 3 hashtags (1 big 500k+ posts, 1 medium 50-500k, 1 niche under 50k)

Return as JSON array, exactly 3 items:
[{{"hook": "...", "angle": "...", "signal_index": 1, "hashtags": ["#Tag1", "#Tag2", "#Tag3"]}}]
No markdown. Only the JSON array."""

    try:
        anthropic = Anthropic(api_key=settings.anthropic_api_key)
        resp = anthropic.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception:
        logger.exception("Angle generation failed")

    return []
