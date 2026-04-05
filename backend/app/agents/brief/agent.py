"""Brief — Doctor Research Agent.

WhatsApp-native agent that:
- Onboards doctors (specialty, institution, focus areas, journals, preferences)
- Sends a personalised morning briefing at 06:30 per client timezone
- Answers follow-up questions about papers and clinical topics
- Updates memory after every interaction using Haiku

Slug: "brief"
"""

from __future__ import annotations

import logging

from anthropic import Anthropic

from app.agents.base import BaseAgent
from app.agents.brief.formatter import format_morning_briefing, update_memory_with_haiku
from app.agents.brief.research import fetch_grok_signals, fetch_pubmed
from app.agents.human_feel import familiarity_prefix
from app.config import settings

logger = logging.getLogger(__name__)

# Onboarding steps
_ONBOARDING_QUESTIONS = [
    # step 0: specialty
    "What's your medical specialty? (e.g. interventional cardiology, oncology, emergency medicine)",
    # step 1: institution
    "Which hospital or clinic are you based at?",
    # step 2: clinical focus
    "What are your 2-3 main clinical focus areas? (e.g. TAVI outcomes, complex PCI, heart failure)",
    # step 3: trusted journals
    "Which journals do you trust most? (e.g. NEJM, JACC, Lancet — just list them)",
    # step 4: dislikes
    "Anything you don't want in your briefing? (e.g. review articles, animal studies, editorials)",
    # step 5: peak reading time (optional)
    "What time do you prefer to receive your briefing? Default is 06:30 your local time. Reply with a time or just say 'default'.",
]


class DoctorBriefAgent(BaseAgent):
    """Brief — personalised daily research briefing for doctors."""

    slug = "brief"
    personality_prompt = (
        "You are Brief, a specialist medical research assistant. "
        "You are knowledgeable, direct, and evidence-driven. "
        "You speak like a trusted senior colleague — no small talk, no fluff. "
        "You know your doctor's specialty deeply and surface only what matters clinically."
    )

    def get_intro_message(self, client: dict) -> str:
        name = client.get("name", "Doctor")
        return (
            f"Good morning, Dr. {name.split()[-1]}. I'm Brief — your daily research assistant.\n\n"
            f"Every morning at 06:30, I'll send you the most relevant papers and clinical signals "
            f"in your specialty. No noise. Just what you need before your first patient.\n\n"
            f"Let me set you up properly. It'll take 2 minutes."
        )

    def get_onboarding_question(self, step: int, collected: dict) -> str | None:
        if step >= len(_ONBOARDING_QUESTIONS):
            return None
        return _ONBOARDING_QUESTIONS[step]

    def process_onboarding_answer(self, step: int, answer: str, collected: dict) -> dict:
        updated = dict(collected)
        answer = answer.strip()

        if step == 0:
            updated["specialty"] = answer
        elif step == 1:
            updated["institution"] = answer
        elif step == 2:
            # Parse comma/newline separated list
            items = [i.strip() for i in answer.replace("\n", ",").split(",") if i.strip()]
            updated["clinical_focus"] = items
        elif step == 3:
            journals = [j.strip() for j in answer.replace("\n", ",").split(",") if j.strip()]
            updated["trusted_journals"] = journals
        elif step == 4:
            dislikes = [d.strip() for d in answer.replace("\n", ",").split(",") if d.strip()]
            updated["dislikes"] = dislikes
        elif step == 5:
            if answer.lower() in ("default", "ok", "yes", "fine", "06:30", "6:30"):
                updated["peak_reading_time"] = "06:30"
            else:
                updated["peak_reading_time"] = answer
            # Final step — build initial memory
            updated.setdefault("familiarity_level", 0)
            updated.setdefault("preferred_format", "3 papers, 2-sentence summary each, link at end")

        return updated

    async def handle_message(
        self,
        client: dict,
        message: dict,
        memory: dict,
        profile: dict,
    ) -> str:
        """Handle an incoming message from the doctor.

        Most messages are follow-up questions about papers — answer them
        using the agent's personality and the doctor's memory context.
        """
        text = message.get("text", "").strip()
        if not text:
            return "I didn't catch that. Try sending a text message or ask me about a paper."

        name = client.get("name", "Doctor")
        familiarity = memory.get("familiarity_level", 0)
        greeting = familiarity_prefix(familiarity, name)
        specialty = memory.get("specialty", "medicine")

        if not settings.anthropic_api_key:
            return f"Got it, {greeting}. (Claude API not configured — can't process this right now.)"

        # Build context from memory + recent message history
        context_parts = []
        if memory:
            context_parts.append(f"Doctor profile:\n{memory}")
        if profile:
            context_parts.append(f"Communication style: {profile.get('communication_style', '')}")

        context = "\n\n".join(context_parts)

        prompt = f"""{self.personality_prompt}

{context}

The doctor just sent: "{text}"

Respond helpfully. If they're asking about a specific paper or clinical topic, give a concise, evidence-based answer.
If they're giving feedback on the briefing format, acknowledge it and note it will be updated.
Keep it under 150 words. WhatsApp-native: short paragraphs, no markdown."""

        try:
            anthropic = Anthropic(api_key=settings.anthropic_api_key)
            message_resp = anthropic.messages.create(
                model="claude-haiku-4-5-20251001",  # fast for interactive replies
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            reply = message_resp.content[0].text.strip()

            # Update memory with this interaction (Haiku)
            interaction_summary = f"Doctor asked: {text}\nBrief replied: {reply}"
            updated_memory = update_memory_with_haiku(memory, interaction_summary)

            # Persist updated memory
            from app.agents.memory import save_agent_memory
            save_agent_memory(client["id"], self.slug, updated_memory)

            return reply

        except Exception:
            logger.exception("Brief handle_message failed for client=%s", client.get("id"))
            return f"Something went wrong on my end, {greeting}. Try again in a moment."

    async def proactive_outreach(
        self,
        client: dict,
        memory: dict,
        profile: dict,
    ) -> str | None:
        """Generate the morning briefing. Called by the scheduler at 06:30."""
        specialty = memory.get("specialty")
        if not specialty:
            logger.info("Brief: no specialty in memory for client=%s — skipping", client.get("id"))
            return None

        clinical_focus = memory.get("clinical_focus", [])
        trusted_journals = memory.get("trusted_journals", [])
        dislikes = memory.get("dislikes", [])

        logger.info(
            "Brief: fetching research for client=%s specialty=%s",
            client.get("id"), specialty,
        )

        # Fetch from both sources concurrently
        import asyncio
        pubmed_task = asyncio.to_thread(
            fetch_pubmed, specialty, clinical_focus, trusted_journals, dislikes
        )
        grok_task = fetch_grok_signals(specialty, clinical_focus)

        pubmed_articles, grok_signals = await asyncio.gather(pubmed_task, grok_task)

        logger.info(
            "Brief: %d PubMed + %d Grok signals for client=%s",
            len(pubmed_articles), len(grok_signals), client.get("id"),
        )

        briefing = format_morning_briefing(memory, profile, pubmed_articles, grok_signals)

        # Update memory after send
        interaction_summary = f"Sent morning briefing with {len(pubmed_articles)} PubMed articles and {len(grok_signals)} X signals."
        updated_memory = update_memory_with_haiku(memory, interaction_summary)

        from app.agents.memory import save_agent_memory, log_message
        save_agent_memory(client["id"], self.slug, updated_memory)
        log_message(
            client_id=client["id"],
            agent_slug=self.slug,
            direction="out",
            message_type="text",
            raw_content=f"Morning briefing — {len(pubmed_articles)} papers, {len(grok_signals)} signals",
            response=briefing,
        )

        return briefing
