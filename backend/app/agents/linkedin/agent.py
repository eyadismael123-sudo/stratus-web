"""LinkedIn Post Agent.

WhatsApp/Telegram-native agent that:
- Onboards clients (role, audience, topics, voice, preferences)
- Sends 3 morning post ideas at 08:00 per client timezone
- Handles post refinement in conversation
- Updates voice profile memory after every interaction

Slug: "linkedin"
"""

from __future__ import annotations

import logging

from anthropic import Anthropic

from app.agents.base import BaseAgent
from app.agents.brief.formatter import update_memory_with_haiku
from app.agents.linkedin.generator import generate_post_ideas
from app.agents.linkedin.research import fetch_linkedin_signals
from app.config import settings

logger = logging.getLogger(__name__)

class LinkedInPostAgent(BaseAgent):
    """LinkedIn Post Agent — daily post ideas in the client's voice."""

    slug = "linkedin"
    personality_prompt = (
        "You are a LinkedIn ghostwriter and thought-leadership coach. "
        "You know your client's industry deeply and write in their exact voice. "
        "You are direct, never sycophantic, and obsessed with creating content "
        "that actually gets engagement — not generic corporate fluff. "
        "Every post you write sounds like a human, not a marketing department."
    )

    _MAX_HISTORY = 20  # max turns kept in memory (user+assistant pairs)

    async def handle_message(
        self,
        client: dict,
        message: dict,
        memory: dict,
        profile: dict,
    ) -> str:
        text = message.get("text", "").strip()
        if not text:
            return "Send me a message — or a number (1/2/3) to refine one of today's ideas."

        if not settings.anthropic_api_key:
            return "Claude API not configured — can't process this right now."

        name = client.get("name", "")
        field = memory.get("field", "your industry")
        audience = memory.get("audience", "professionals")
        voice_tone = memory.get("voice_tone", "professional")
        topics = memory.get("topics", [])
        style_notes = memory.get("style_notes", [])
        avoid = memory.get("avoid", [])

        topics_note = f"Their go-to topics: {', '.join(topics)}." if topics else ""
        avoid_note = f"Never write about: {', '.join(avoid)}." if avoid else ""
        style_note = f"Style notes: {'; '.join(style_notes)}." if style_notes else ""

        system_prompt = f"""{self.personality_prompt}

Client profile:
- Name: {name}
- Field: {field}
- Audience: {audience}
- Voice: {voice_tone}
- {topics_note}
- {style_note}
- {avoid_note}

You know this client's voice and topics well — use them. If they want to make a post,
pick the most relevant topic from their list and write a full draft immediately.
Don't ask what they want to write about — you already know.
If they're asking to refine a post idea, rewrite it in their voice.
If they're giving feedback, acknowledge and adapt.
Keep replies under 250 words. No markdown — plain text for Telegram."""

        # Build multi-turn conversation history
        history: list[dict] = memory.get("conversation_history", [])
        messages = [*history, {"role": "user", "content": text}]

        try:
            anthropic = Anthropic(api_key=settings.anthropic_api_key)
            resp = anthropic.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                system=system_prompt,
                messages=messages,
            )
            reply = resp.content[0].text.strip()

            # Append this turn and trim to window
            updated_history = [
                *history,
                {"role": "user", "content": text},
                {"role": "assistant", "content": reply},
            ]
            updated_history = updated_history[-(self._MAX_HISTORY * 2):]

            interaction_summary = f"Client said: {text}\nAgent replied: {reply}"
            updated_memory = update_memory_with_haiku(memory, interaction_summary)
            updated_memory = {**updated_memory, "conversation_history": updated_history}

            from app.agents.memory import save_agent_memory
            save_agent_memory(client["id"], self.slug, updated_memory)

            return reply

        except Exception:
            logger.exception("LinkedIn handle_message failed for client=%s", client.get("id"))
            return "Something went wrong — try again in a moment."

    async def proactive_outreach(
        self,
        client: dict,
        memory: dict,
        profile: dict,
    ) -> str | None:
        field = memory.get("field")
        if not field:
            logger.info("LinkedIn: no field in memory for client=%s — skipping", client.get("id"))
            return None

        audience = memory.get("audience", "professionals")
        topics = memory.get("topics", [])

        logger.info(
            "LinkedIn: fetching signals for client=%s field=%s",
            client.get("id"), field,
        )

        signals = await fetch_linkedin_signals(field, audience, topics)

        logger.info(
            "LinkedIn: %d signals for client=%s",
            len(signals), client.get("id"),
        )

        ideas = generate_post_ideas(memory, profile, signals)

        from app.agents.linkedin.generator import format_briefing_message
        briefing = format_briefing_message(ideas, client.get("name", ""))

        interaction_summary = f"Sent morning briefing with {len(ideas)} post ideas."
        updated_memory = update_memory_with_haiku(memory, interaction_summary)

        from app.agents.memory import save_agent_memory, log_message
        save_agent_memory(client["id"], self.slug, updated_memory)
        log_message(
            client_id=client["id"],
            agent_slug=self.slug,
            direction="out",
            message_type="text",
            raw_content=f"Morning briefing — {len(ideas)} post ideas",
            response=briefing,
        )

        return briefing


def _upsert_linkedin_memory(collected: dict) -> None:
    """Persist structured fields to the linkedin_memory table after onboarding."""
    try:
        from app.db.connection import get_service_client
        from datetime import datetime, timezone

        client_id = collected.get("client_id")
        if not client_id:
            return

        db = get_service_client()
        db.table("linkedin_memory").upsert(
            {
                "client_id": client_id,
                "field": collected.get("field", ""),
                "audience": collected.get("audience", ""),
                "region": collected.get("region", "UAE"),
                "post_time": collected.get("post_time", "08:00"),
                "post_frequency": collected.get("post_frequency", "daily"),
                "voice_profile": {
                    "voice_tone": collected.get("voice_tone", ""),
                    "avoid": collected.get("avoid", []),
                    "topics": collected.get("topics", []),
                },
                "style_notes": collected.get("style_notes", []),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            on_conflict="client_id",
        ).execute()
    except Exception:
        logger.exception("Failed to upsert linkedin_memory for client")
