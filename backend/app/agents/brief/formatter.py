"""Briefing formatter for Brief (Doctor Research Agent).

Uses Claude Sonnet to format raw PubMed + Grok signals into a personalised
morning briefing in the doctor's voice, based on their agent memory.

Sonnet is used here (not Haiku) — this is a quality task per the framework spec.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from anthropic import Anthropic

from app.config import settings

logger = logging.getLogger(__name__)

_anthropic: Anthropic | None = None


def _get_anthropic() -> Anthropic:
    global _anthropic
    if _anthropic is None:
        _anthropic = Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic


def format_morning_briefing(
    memory: dict,
    profile: dict,
    pubmed_articles: list[dict],
    grok_signals: list[dict],
) -> str:
    """Generate a personalised morning briefing using Sonnet.

    Args:
        memory:  Layer 2 agent memory (specialty, clinical_focus, preferred_format, etc.)
        profile: Layer 3 master profile (communication_style, familiarity_trajectory, etc.)
        pubmed_articles: List of article dicts from PubMed
        grok_signals:    List of signal dicts from Grok/X

    Returns:
        Plain-text briefing ready to send via WhatsApp.
    """
    specialty = memory.get("specialty", "medicine")
    institution = memory.get("institution", "")
    clinical_focus = memory.get("clinical_focus", [])
    preferred_format = memory.get("preferred_format", "3 papers, 2-sentence summary each, link at end")
    familiarity_level = memory.get("familiarity_level", 0)
    dislikes = memory.get("dislikes", [])

    comm_style = profile.get("communication_style", "professional")
    familiarity_note = profile.get("familiarity_trajectory", "")

    today = datetime.now(timezone.utc).strftime("%A, %B %d")

    # Build raw content block
    raw_sections: list[str] = []

    if pubmed_articles:
        articles_text = "\n".join(
            f"- {a['title']} | {a['journal']} ({a['pub_date']}) | {a['url']}"
            for a in pubmed_articles
        )
        raw_sections.append(f"PUBMED (last 14 days):\n{articles_text}")

    if grok_signals:
        signals_text = "\n".join(
            f"- {s.get('title', '')} — {s.get('summary', '')} [{s.get('source', 'X')}]"
            for s in grok_signals
        )
        raw_sections.append(f"X/TWITTER CLINICAL SIGNALS:\n{signals_text}")

    if not raw_sections:
        today_str = datetime.now(timezone.utc).strftime("%A, %B %d")
        return (
            f"Good morning — {today_str}\n\n"
            f"No major updates in {specialty} overnight. "
            f"Clear morning to focus on your patients."
        )

    raw_content = "\n\n".join(raw_sections)

    # Tone calibration based on familiarity
    tone_note = ""
    if familiarity_level <= 1:
        tone_note = "Tone: formal and professional."
    elif familiarity_level <= 3:
        tone_note = "Tone: collegial — like a trusted colleague. Can use first-name basis."
    else:
        tone_note = "Tone: casual and direct — you've built a real working relationship."

    if familiarity_note:
        tone_note += f" Context: {familiarity_note}."

    dislike_note = f"Avoid: {', '.join(dislikes)}." if dislikes else ""

    prompt = f"""You are Brief, a specialist AI research assistant for a {specialty} doctor{f' at {institution}' if institution else ''}.

Today is {today}.

Your doctor's preferred format: {preferred_format}
{tone_note}
{dislike_note}

Raw clinical information gathered this morning:

{raw_content}

Write a morning briefing for WhatsApp. Rules:
- No markdown symbols (no **, no #, no bullet dashes with markdown)
- Use plain text with line breaks
- Follow the doctor's preferred format exactly
- Focus on {', '.join(clinical_focus[:2]) if clinical_focus else specialty}
- End with one practical takeaway for their day
- Under 300 words total
- WhatsApp-native: short paragraphs, readable on a phone screen"""

    if not settings.anthropic_api_key:
        logger.warning("No ANTHROPIC_API_KEY — using fallback briefing")
        return _fallback(specialty, pubmed_articles, grok_signals)

    try:
        message = _get_anthropic().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    except Exception:
        logger.exception("Sonnet formatting failed — falling back to raw format")
        return _fallback(specialty, pubmed_articles, grok_signals)


def _fallback(
    specialty: str,
    pubmed_articles: list[dict],
    grok_signals: list[dict],
) -> str:
    today = datetime.now(timezone.utc).strftime("%A, %B %d")
    lines = [f"Good morning — {today}", "", f"Today in {specialty}:"]
    for a in pubmed_articles[:3]:
        lines.append(f"\n{a['title']}\n{a['journal']} | {a['url']}")
    for s in grok_signals[:2]:
        lines.append(f"\nX: {s.get('title', '')} — {s.get('summary', '')}")
    return "\n".join(lines)


def update_memory_with_haiku(
    memory: dict,
    interaction_summary: str,
) -> dict:
    """Use Haiku to update agent memory after a briefing or interaction.

    Cheap + fast — runs after every send.
    Updates familiarity_level, preferred_format, dislikes based on feedback.
    Returns the updated memory dict.
    """
    if not settings.anthropic_api_key:
        return memory

    prompt = f"""Current agent memory (JSON):
{memory}

New interaction summary:
{interaction_summary}

Update the memory JSON to reflect what you learned. Rules:
- Increment familiarity_level (max 5) only if the doctor engaged positively
- Update preferred_format if the doctor expressed a preference
- Add to dislikes if the doctor said something was unhelpful
- Keep all existing fields, only update what's relevant
- Return ONLY valid JSON, no explanation"""

    try:
        anthropic = _get_anthropic()
        message = anthropic.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        text = message.content[0].text.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception:
        logger.exception("Haiku memory update failed — keeping current memory")

    return memory
