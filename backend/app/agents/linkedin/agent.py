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

_ONBOARDING_QUESTIONS = [
    # step 0: role and field
    "What's your role and industry? (e.g. 'Regional Sales Manager at AbbVie Pharmaceuticals')",
    # step 1: target audience
    "Who do you want to reach on LinkedIn? (e.g. 'Cardiologists and GPs in the UAE')",
    # step 2: core topics
    "What topics do you want to build authority in? (e.g. 'pharma innovation, patient outcomes, leadership')",
    # step 3: voice and tone
    "How would you describe your voice? (e.g. 'Authoritative but human. I use data but also tell stories.')",
    # step 4: avoid list
    "Anything to avoid in your posts? (e.g. 'no politics, no competitor mentions') — or reply 'none'",
    # step 5: briefing time
    "What time should I send your morning briefing? Default is 08:00 your local time. Reply with a time or 'default'.",
]


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

    def get_intro_message(self, client: dict) -> str:
        name = client.get("name", "")
        first = name.split()[0] if name else "there"
        return (
            f"Hey {first}! I'm your LinkedIn Post Agent.\n\n"
            f"Every morning at 08:00, I'll send you 3 post ideas written in your voice — "
            f"based on what's trending in your industry right now.\n\n"
            f"Takes 2 minutes to set up. Let's go."
        )

    def get_onboarding_question(self, step: int, collected: dict) -> str | None:
        if step >= len(_ONBOARDING_QUESTIONS):
            return None
        return _ONBOARDING_QUESTIONS[step]

    def process_onboarding_answer(self, step: int, answer: str, collected: dict) -> dict:
        updated = dict(collected)
        answer = answer.strip()

        if step == 0:
            updated["field"] = answer
        elif step == 1:
            updated["audience"] = answer
        elif step == 2:
            items = [i.strip() for i in answer.replace("\n", ",").split(",") if i.strip()]
            updated["topics"] = items
        elif step == 3:
            updated["voice_tone"] = answer
        elif step == 4:
            if answer.lower() in ("none", "no", "nothing", "-", "n/a"):
                updated["avoid"] = []
            else:
                items = [i.strip() for i in answer.replace("\n", ",").split(",") if i.strip()]
                updated["avoid"] = items
        elif step == 5:
            if answer.lower() in ("default", "ok", "yes", "fine", "08:00", "8:00", "8am"):
                updated["post_time"] = "08:00"
            else:
                updated["post_time"] = answer
            updated.setdefault("familiarity_level", 0)
            updated.setdefault("style_notes", [])

            # Write structured fields to linkedin_memory table
            _upsert_linkedin_memory(updated)

        return updated

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

        name = client.get("name", "")
        familiarity = memory.get("familiarity_level", 0)

        if not settings.anthropic_api_key:
            return "Claude API not configured — can't process this right now."

        field = memory.get("field", "your industry")
        voice_tone = memory.get("voice_tone", "professional")
        avoid = memory.get("avoid", [])
        avoid_note = f"Avoid: {', '.join(avoid)}." if avoid else ""

        prompt = f"""{self.personality_prompt}

Client: {name}
Field: {field}
Voice: {voice_tone}
{avoid_note}

The client just sent: "{text}"

If they're asking to refine a post idea (they may say "refine idea 1" or just "make it shorter"
or "more personal"), rewrite the relevant post accordingly.
If they're giving feedback on their voice or preferences, acknowledge and note it.
If they're asking a question about LinkedIn strategy, give a direct, expert answer.
Keep replies under 200 words. No markdown — plain text for Telegram."""

        try:
            anthropic = Anthropic(api_key=settings.anthropic_api_key)
            resp = anthropic.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            reply = resp.content[0].text.strip()

            interaction_summary = f"Client said: {text}\nAgent replied: {reply}"
            updated_memory = update_memory_with_haiku(memory, interaction_summary)

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
