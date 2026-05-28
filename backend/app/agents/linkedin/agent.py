"""LinkedIn Post Agent.

WhatsApp/Telegram-native agent that:
- Sends 3 morning post ideas at 08:00 per client timezone
- On-demand: researches trending angles via Grok, presents options as Telegram buttons
- Handles post refinement in conversation
- Updates voice profile memory after every interaction

Slug: "linkedin"
"""

from __future__ import annotations

import logging
from urllib.parse import quote

from anthropic import Anthropic

from app.agents.base import BaseAgent
from app.agents.brief.formatter import update_memory_with_haiku
from app.agents.linkedin.generator import generate_post_ideas
from app.agents.linkedin.research import (
    fetch_all_signals,
    generate_angles_from_signals,
)
from app.config import settings

logger = logging.getLogger(__name__)

_LINKEDIN_NEW_POST_URL = "https://www.linkedin.com/feed/?shareActive=true&text={text}"

_LINKEDIN_CRAFT = """
LinkedIn post craft principles (always apply these):
- NEVER open with "I" — proven engagement killer
- Hook: 1-2 lines, creates tension or curiosity. Types: bold claim, time+place story opener,
  counterintuitive take, pattern interrupt, specific question
- Body: short paragraphs (1-3 lines), white space, mobile-first reading
- Length: 1200-1800 characters — delivers value without losing them
- End with a real question that invites comment, not "do you agree?"
- Specificity always beats generality: "Day 47 of surgery rotation" > "during med school"
- No corporate speak, no "excited to share", no "thoughts?"
- Hashtags: 3-5 at the very end — 1 broad (500k+ posts), 1 medium (50-500k), 1 niche (<50k)
- Vulnerability and honesty outperform polished advice every time
"""


def _detect_intent(text: str) -> str:
    """Classify user intent: new_post | refine | question | other."""
    lowered = text.lower()
    words = set(lowered.split())

    # Exact phrase matches
    new_post_phrases = [
        "make a post", "write a post", "new post", "create a post",
        "post idea", "wanna post", "generate a post", "draft a post",
        "i want a post", "write me a post", "help me post", "let's post",
        "write up a post", "post something", "lets post", "make post",
    ]
    # Word-pair combos — catches "write up a post", "ts write a post", etc.
    new_post_pairs = [
        ("write", "post"), ("make", "post"), ("create", "post"),
        ("draft", "post"), ("generate", "post"), ("need", "post"),
        ("want", "post"), ("post", "today"), ("post", "now"),
    ]
    refine_kws = [
        "refine", "shorter", "longer", "make it", "rewrite", "change it",
        "edit", "idea 1", "idea 2", "idea 3", "option 1", "option 2",
        "more personal", "stronger hook", "too long", "too short",
    ]
    if any(phrase in lowered for phrase in new_post_phrases):
        return "new_post"
    if any(a in words and b in words for a, b in new_post_pairs):
        return "new_post"
    if any(kw in lowered for kw in refine_kws):
        return "refine"
    if "?" in text or any(kw in lowered for kw in ["how do", "why", "should i", "advice", "strategy", "tip", "what if"]):
        return "question"
    return "other"


class LinkedInPostAgent(BaseAgent):
    """LinkedIn Post Agent — daily post ideas + on-demand research-backed drafts."""

    slug = "linkedin"
    personality_prompt = (
        "You are a LinkedIn ghostwriter and thought-leadership coach for a medical student. "
        "You write in their exact voice — honest, specific, never corporate. "
        "You are direct, never sycophantic, and obsessed with posts that actually get engagement. "
        "Every post sounds like a human being, not a marketing department. "
        + _LINKEDIN_CRAFT
    )

    _MAX_HISTORY = 20

    async def handle_message(
        self,
        client: dict,
        message: dict,
        memory: dict,
        profile: dict,
    ) -> str | dict:
        text = message.get("text", "").strip()
        if not text:
            return "Send me a message — or tap a button to pick a post angle."

        if not settings.anthropic_api_key:
            return "Claude API not configured."

        intent = _detect_intent(text)

        if intent == "new_post":
            return await self._research_and_present_angles(client, memory, profile)

        return await self._converse(text, client, memory, profile)

    async def handle_callback(
        self,
        callback_data: str,
        client: dict,
        memory: dict,
        profile: dict,
    ) -> str | dict:
        """Handle Telegram inline keyboard button presses."""
        if callback_data.startswith("angle:"):
            idx = int(callback_data.split(":")[1])
            return await self._draft_from_angle(idx, client, memory, profile)

        if callback_data.startswith("refine:"):
            instruction = callback_data.split(":", 1)[1]
            return await self._refine_draft(instruction, client, memory, profile)

        if callback_data == "action:linkedin":
            draft = memory.get("current_draft", "")
            if not draft:
                return "No draft saved — ask me to write a post first."
            url = _LINKEDIN_NEW_POST_URL.format(text=quote(draft[:700]))
            return f"Post to LinkedIn:\n{url}"

        return "Unknown action."

    # ------------------------------------------------------------------
    # Internal: research → angles
    # ------------------------------------------------------------------

    async def _research_and_present_angles(
        self,
        client: dict,
        memory: dict,
        profile: dict,
    ) -> str | dict:
        field = memory.get("field", "your industry")
        audience = memory.get("audience", "professionals")
        topics = memory.get("topics", [])

        signals = await fetch_all_signals(field, audience, topics)
        if not signals:
            return "Research came back empty — web search is down. Try again in a minute."

        angles = await generate_angles_from_signals(signals, memory)
        if not angles:
            return "Got the research but couldn't generate angles — try again."

        updated_memory = {**memory, "pending_angles": angles, "pending_signals": signals}
        from app.agents.memory import save_agent_memory
        save_agent_memory(client["id"], self.slug, updated_memory)

        options = [
            {"label": f"{['1️⃣','2️⃣','3️⃣'][i]} {a['hook']}", "data": f"angle:{i}"}
            for i, a in enumerate(angles[:3])
        ]

        return {
            "text": "Done the research. Pick an angle:",
            "options": options,
        }

    # ------------------------------------------------------------------
    # Internal: draft from selected angle
    # ------------------------------------------------------------------

    async def _draft_from_angle(
        self,
        angle_idx: int,
        client: dict,
        memory: dict,
        profile: dict,
    ) -> str | dict:
        angles = memory.get("pending_angles", [])
        if not angles or angle_idx >= len(angles):
            return "Angle not found — ask me to research again."

        angle = angles[angle_idx]
        signals = memory.get("pending_signals", [])
        signal = signals[angle.get("signal_index", 1) - 1] if signals else {}

        name = client.get("name", "")
        field = memory.get("field", "")
        voice_tone = memory.get("voice_tone", "professional")
        avoid = memory.get("avoid", [])
        style_notes = memory.get("style_notes", [])

        hashtags = angle.get("hashtags", ["#MedStudent", "#LinkedIn"])
        hashtag_str = " ".join(hashtags)

        prompt = f"""Write a full LinkedIn post for {name}, a {field} professional.

Voice: {voice_tone}
Style notes: {'; '.join(style_notes) if style_notes else 'none'}
Never write about: {', '.join(avoid) if avoid else 'nothing off limits'}

Hook to use (first line): {angle['hook']}
Angle/insight: {angle['angle']}
Research context: {signal.get('summary', '')}

{_LINKEDIN_CRAFT}

Write the full post now. End with: {hashtag_str}
Plain text only, no markdown. No meta-commentary — just the post."""

        try:
            anthropic = Anthropic(api_key=settings.anthropic_api_key)
            resp = anthropic.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=700,
                messages=[{"role": "user", "content": prompt}],
            )
            draft = resp.content[0].text.strip()

            # Store draft for refinement + LinkedIn URL
            updated_memory = {**memory, "current_draft": draft, "current_hashtags": hashtags}
            from app.agents.memory import save_agent_memory
            save_agent_memory(client["id"], self.slug, updated_memory)

            linkedin_url = _LINKEDIN_NEW_POST_URL.format(text=quote(draft[:700]))

            return {
                "text": draft,
                "options": [
                    {"label": "✂️ Shorter", "data": "refine:shorter"},
                    {"label": "💬 More personal", "data": "refine:personal"},
                    {"label": "🎣 Stronger hook", "data": "refine:hook"},
                    {"label": "🚀 Post to LinkedIn", "data": "action:linkedin"},
                ],
            }

        except Exception:
            logger.exception("Draft generation failed for client=%s", client.get("id"))
            return "Draft failed — try again."

    # ------------------------------------------------------------------
    # Internal: refine existing draft
    # ------------------------------------------------------------------

    async def _refine_draft(
        self,
        instruction: str,
        client: dict,
        memory: dict,
        profile: dict,
    ) -> str | dict:
        draft = memory.get("current_draft", "")
        if not draft:
            return "No draft to refine — ask me to write a post first."

        instructions_map = {
            "shorter": "Cut it to under 900 characters. Keep the hook and the core insight. Remove anything that doesn't add value.",
            "personal": "Make it more personal and vulnerable. Add a specific moment or feeling. Less advice, more story.",
            "hook": "Rewrite just the first 1-2 lines. Make the hook impossible to scroll past. Try a bold claim or a story opener.",
        }

        refinement = instructions_map.get(instruction, f"Refine this post: {instruction}")

        name = client.get("name", "")
        voice_tone = memory.get("voice_tone", "professional")

        prompt = f"""Refine this LinkedIn post for {name}.
Voice: {voice_tone}

Original post:
{draft}

Instruction: {refinement}

{_LINKEDIN_CRAFT}

Return only the refined post. No meta-commentary. Plain text."""

        try:
            anthropic = Anthropic(api_key=settings.anthropic_api_key)
            resp = anthropic.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=700,
                messages=[{"role": "user", "content": prompt}],
            )
            refined = resp.content[0].text.strip()

            updated_memory = {**memory, "current_draft": refined}
            from app.agents.memory import save_agent_memory
            save_agent_memory(client["id"], self.slug, updated_memory)

            return {
                "text": refined,
                "options": [
                    {"label": "✂️ Shorter", "data": "refine:shorter"},
                    {"label": "💬 More personal", "data": "refine:personal"},
                    {"label": "🎣 Stronger hook", "data": "refine:hook"},
                    {"label": "🚀 Post to LinkedIn", "data": "action:linkedin"},
                ],
            }

        except Exception:
            logger.exception("Refinement failed for client=%s", client.get("id"))
            return "Refinement failed — try again."

    # ------------------------------------------------------------------
    # Internal: general conversation with history
    # ------------------------------------------------------------------

    async def _converse(
        self,
        text: str,
        client: dict,
        memory: dict,
        profile: dict,
    ) -> str:
        name = client.get("name", "")
        field = memory.get("field", "your industry")
        audience = memory.get("audience", "professionals")
        voice_tone = memory.get("voice_tone", "professional")
        topics = memory.get("topics", [])
        style_notes = memory.get("style_notes", [])
        avoid = memory.get("avoid", [])

        system_prompt = f"""{self.personality_prompt}

Client profile:
- Name: {name}
- Field: {field}
- Audience: {audience}
- Voice: {voice_tone}
- Topics: {', '.join(topics) if topics else 'not set'}
- Style: {'; '.join(style_notes) if style_notes else 'none'}
- Never write about: {', '.join(avoid) if avoid else 'nothing off limits'}

Keep replies under 200 words. Plain text for Telegram. No markdown."""

        history: list[dict] = memory.get("conversation_history", [])
        messages = [*history, {"role": "user", "content": text}]

        try:
            anthropic = Anthropic(api_key=settings.anthropic_api_key)
            resp = anthropic.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                system=system_prompt,
                messages=messages,
            )
            reply = resp.content[0].text.strip()

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
            logger.exception("LinkedIn converse failed for client=%s", client.get("id"))
            return "Something went wrong — try again."

    # ------------------------------------------------------------------
    # Proactive outreach (morning briefing)
    # ------------------------------------------------------------------

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

        signals = await fetch_all_signals(field, audience, topics)
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
