"""Post idea generator for the LinkedIn Post Agent.

Uses Claude Sonnet to turn Grok signals into 3 LinkedIn post drafts
in the client's exact voice, ready to copy-paste or refine.
"""

from __future__ import annotations

import json
import logging
from urllib.parse import quote

from anthropic import Anthropic

from app.config import settings

logger = logging.getLogger(__name__)

_LINKEDIN_NEW_POST_URL = "https://www.linkedin.com/feed/?shareActive=true&text={text}"

_anthropic: Anthropic | None = None


def _get_anthropic() -> Anthropic:
    global _anthropic
    if _anthropic is None:
        _anthropic = Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic


def _linkedin_url(post_text: str) -> str:
    """Build a LinkedIn pre-fill link for a post draft."""
    encoded = quote(post_text[:700])  # LinkedIn caps deep-link text
    return _LINKEDIN_NEW_POST_URL.format(text=encoded)


def generate_post_ideas(
    memory: dict,
    profile: dict,
    signals: list[dict],
) -> list[dict]:
    """Generate 3 LinkedIn post ideas in the client's voice.

    Args:
        memory:  Layer 2 agent memory (field, audience, topics, voice_tone, etc.)
        profile: Layer 3 master profile (communication_style, etc.)
        signals: Grok research signals [{title, summary, angle, source}]

    Returns:
        List of up to 3 dicts: {topic, hook, draft, linkedin_url}
    """
    if not settings.anthropic_api_key:
        logger.warning("No ANTHROPIC_API_KEY — cannot generate post ideas")
        return []

    field = memory.get("field", "")
    audience = memory.get("audience", "professionals")
    topics = memory.get("topics", [])
    voice_tone = memory.get("voice_tone", "professional and thoughtful")
    style_notes = memory.get("style_notes", [])
    comm_style = profile.get("communication_style", "")

    voice_description = voice_tone
    if style_notes:
        voice_description += f". Style notes: {'; '.join(style_notes[:3])}"
    if comm_style:
        voice_description += f". Communication style: {comm_style}"

    if signals:
        signals_text = "\n".join(
            f"- {s.get('title', '')} | Angle: {s.get('angle', '')} | "
            f"Summary: {s.get('summary', '')} [{s.get('source', '')}]"
            for s in signals[:5]
        )
        research_block = f"Today's research signals:\n{signals_text}"
    else:
        focus = ", ".join(topics[:3]) if topics else field
        research_block = f"Topics to write about: {focus}"

    prompt = f"""You are a LinkedIn ghostwriter for a {field} professional.

Their audience: {audience}
Their voice: {voice_description}

{research_block}

Write exactly 3 LinkedIn post ideas. Each idea must be:
- A full draft ready to post (150-250 words)
- Written in first person, in the client's voice
- Opening with a strong hook (no "I am..." or "Today I want to...")
- No hashtags in the body — add 2-3 at the very end only
- Professional LinkedIn format: short paragraphs, no bullet walls
- Each genuinely different in angle and format (e.g. story, insight, question)

Return as a JSON array with exactly 3 items:
[{{"topic": "short topic label", "hook": "first line only", "draft": "full post text"}}]
No markdown. Only the JSON array."""

    try:
        message = _get_anthropic().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        start = text.find("[")
        end = text.rfind("]") + 1

        if start >= 0 and end > start:
            ideas = json.loads(text[start:end])
            return [
                {
                    "topic": idea.get("topic", ""),
                    "hook": idea.get("hook", ""),
                    "draft": idea.get("draft", ""),
                    "linkedin_url": _linkedin_url(idea.get("draft", "")),
                }
                for idea in ideas[:3]
            ]

    except Exception:
        logger.exception("Post idea generation failed for field=%s", field)

    return []


def format_briefing_message(ideas: list[dict], name: str = "") -> str:
    """Format the 3 post ideas into a Telegram-ready message."""
    greeting = f"Good morning{', ' + name.split()[0] if name else ''}! "
    header = greeting + "Here are 3 LinkedIn post ideas for today.\n\n"

    if not ideas:
        return header + "No ideas generated today — try again in a moment."

    parts = []
    for i, idea in enumerate(ideas, 1):
        parts.append(
            f"{'📌' if i == 1 else '💡' if i == 2 else '🔥'} IDEA {i}: {idea['topic'].upper()}\n\n"
            f"{idea['draft']}\n\n"
            f"👉 Post on LinkedIn: {idea['linkedin_url']}"
        )

    return header + "\n\n---\n\n".join(parts) + "\n\nReply with the idea number to refine it, or send feedback."
