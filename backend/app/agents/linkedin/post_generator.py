"""Post generation using voice profile + Claude Sonnet.

Generates 2 distinct versions of a LinkedIn post for a given topic,
written in the user's exact extracted voice.
"""

from __future__ import annotations

import logging
from typing import NamedTuple

from anthropic import Anthropic

from app.config import settings

logger = logging.getLogger(__name__)


class PostVersions(NamedTuple):
    version_a: str
    version_b: str


_PROMPT = """You are a professional ghostwriter. Write a LinkedIn post for {name} about this topic:

TOPIC: {topic}
ANGLE: {angle}

Match their voice profile exactly:
- Tone: {tone}
- Sentence patterns: {sentence_patterns}
- Formatting style: {formatting_style}
- Signature phrases (weave in naturally): {signature_phrases}
- Emoji usage: {emoji_usage}
- Post length: {post_length}
- How they open posts: {engagement_hooks}
- How they end posts: {calls_to_action}

Voice summary: {voice_summary}{style_notes_section}

Generate TWO versions. Version A and Version B must have different opening hooks but both must sound authentically like {name}.

Return in this exact format — no extra commentary:
VERSION_A:
[post content here]

VERSION_B:
[post content here]"""

_EDIT_PROMPT = """You are a professional ghostwriter. The user gave feedback on LinkedIn post drafts.

TOPIC: {topic}
USER FEEDBACK: "{edit_instruction}"

PREVIOUS VERSION A:
{version_a}

PREVIOUS VERSION B:
{version_b}

Voice profile:
- Tone: {tone}
- Sentence patterns: {sentence_patterns}
- Formatting style: {formatting_style}
- Signature phrases: {signature_phrases}
- Emoji usage: {emoji_usage}
- Post length: {post_length}
- Engagement hooks: {engagement_hooks}
- Calls to action: {calls_to_action}

Voice summary: {voice_summary}{style_notes_section}

Rewrite both versions incorporating the feedback. Keep the same topic and voice — just apply the requested change.

Return in this exact format — no extra commentary:
VERSION_A:
[post content here]

VERSION_B:
[post content here]"""


def _build_style_notes_section(style_notes: list[str]) -> str:
    if not style_notes:
        return ""
    notes = "\n".join(f"- {n}" for n in style_notes)
    return f"\n\nLearned style preferences (apply these):\n{notes}"


def generate_post_versions(
    topic: str,
    angle: str,
    name: str,
    voice_profile: dict,
    style_notes: list[str] | None = None,
) -> PostVersions:
    """Generate 2 post versions for the given topic using the voice profile.

    Returns PostVersions(version_a, version_b). Both strings are empty on failure.
    """
    if not settings.anthropic_api_key:
        logger.warning("No ANTHROPIC_API_KEY — cannot generate posts")
        return PostVersions("", "")

    voice_kwargs = _voice_kwargs(voice_profile)
    prompt = _PROMPT.format(
        name=name or "the author",
        topic=topic,
        angle=angle or "professional insight",
        style_notes_section=_build_style_notes_section(style_notes or []),
        **voice_kwargs,
    )

    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1400,
            messages=[{"role": "user", "content": prompt}],
        )
        return _parse_versions(resp.content[0].text.strip())

    except Exception:
        logger.exception("Post generation failed for topic=%r", topic)
        return PostVersions("", "")


def generate_edited_versions(
    topic: str,
    edit_instruction: str,
    version_a: str,
    version_b: str,
    name: str,
    voice_profile: dict,
    style_notes: list[str] | None = None,
) -> PostVersions:
    """Regenerate posts incorporating user's edit feedback.

    Returns PostVersions(version_a, version_b). Both strings are empty on failure.
    """
    if not settings.anthropic_api_key:
        logger.warning("No ANTHROPIC_API_KEY — cannot regenerate posts")
        return PostVersions("", "")

    voice_kwargs = _voice_kwargs(voice_profile)
    prompt = _EDIT_PROMPT.format(
        topic=topic,
        edit_instruction=edit_instruction,
        version_a=version_a,
        version_b=version_b,
        name=name or "the author",
        style_notes_section=_build_style_notes_section(style_notes or []),
        **voice_kwargs,
    )

    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1400,
            messages=[{"role": "user", "content": prompt}],
        )
        return _parse_versions(resp.content[0].text.strip())

    except Exception:
        logger.exception("Post edit failed for topic=%r edit=%r", topic, edit_instruction)
        return PostVersions("", "")


def _voice_kwargs(voice_profile: dict) -> dict:
    return {
        "tone": voice_profile.get("tone", "professional"),
        "sentence_patterns": ", ".join(voice_profile.get("sentence_patterns", [])),
        "formatting_style": voice_profile.get("formatting_style", "clear paragraphs"),
        "signature_phrases": ", ".join(voice_profile.get("signature_phrases", [])),
        "emoji_usage": voice_profile.get("emoji_usage", "minimal"),
        "post_length": voice_profile.get("post_length", "medium"),
        "engagement_hooks": ", ".join(voice_profile.get("engagement_hooks", [])),
        "calls_to_action": ", ".join(voice_profile.get("calls_to_action", [])),
        "voice_summary": voice_profile.get("voice_summary", ""),
    }


def _parse_versions(raw: str) -> PostVersions:
    """Parse 'VERSION_A:\n...\n\nVERSION_B:\n...' format."""
    parts = raw.split("VERSION_B:")
    if len(parts) != 2:
        logger.warning("Post generator: unexpected format, splitting in half")
        mid = len(raw) // 2
        return PostVersions(raw[:mid].strip(), raw[mid:].strip())

    version_a = parts[0].replace("VERSION_A:", "").strip()
    version_b = parts[1].strip()
    return PostVersions(version_a, version_b)
