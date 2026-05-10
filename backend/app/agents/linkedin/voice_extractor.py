"""Voice profile extraction from LinkedIn posts.

Uses Claude Sonnet to analyze a user's writing style and produce a
structured voice profile used to ghostwrite future posts in their voice.
"""

from __future__ import annotations

import json
import logging

from anthropic import Anthropic

from app.config import settings

logger = logging.getLogger(__name__)

_PROMPT = """You are a professional ghostwriter analyzing a LinkedIn creator's writing style.

Here are {n} LinkedIn posts from {name}:

{posts_block}

Analyze these posts and produce a JSON voice profile. Return ONLY valid JSON, no markdown:

{{
  "tone": "e.g. 'authoritative but approachable', 'casual and witty', 'inspirational'",
  "sentence_patterns": ["3-5 patterns, e.g. 'short punchy sentences', 'rhetorical questions to open'"],
  "formatting_style": "e.g. 'bullet-heavy', 'flowing prose', 'line breaks after every sentence'",
  "signature_phrases": ["phrases or words they repeat, e.g. 'the truth is', 'here's what I learned'"],
  "topics_frequent": ["main topics they write about"],
  "emoji_usage": "none | minimal | moderate | heavy",
  "post_length": "short (< 150 words) | medium (150-300 words) | long (300+ words)",
  "engagement_hooks": ["2-3 ways they typically open posts, e.g. 'bold claim', 'personal story', 'question'"],
  "calls_to_action": ["how they end posts, e.g. 'asks for opinions', 'invites connection'"],
  "voice_summary": "2-3 sentences capturing their unique voice and how to replicate it"
}}"""


def extract_voice_profile(posts: list[str], name: str) -> dict:
    """Analyze LinkedIn posts and extract a structured voice profile.

    Args:
        posts: List of post text strings (ideally 5-10 posts).
        name: Creator's name for context in the prompt.

    Returns:
        Voice profile dict, or empty dict on failure.
    """
    if not posts or not settings.anthropic_api_key:
        return {}

    capped = posts[:10]
    posts_block = "\n\n---\n\n".join(
        f"POST {i + 1}:\n{post.strip()}" for i, post in enumerate(capped)
    )

    prompt = _PROMPT.format(n=len(capped), name=name, posts_block=posts_block)

    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()

        # Strip markdown fences if Claude wrapped in ```json
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        return json.loads(raw.strip())

    except json.JSONDecodeError:
        logger.exception("Voice extraction: Claude returned invalid JSON")
        return {}
    except Exception:
        logger.exception("Voice extraction failed for name=%r", name)
        return {}
