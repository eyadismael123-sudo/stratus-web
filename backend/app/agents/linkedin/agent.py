"""LinkedIn Ghostwriter Agent.

Telegram-native agent that:
1. Onboards users: industry → paste posts → set time → posting frequency
2. Daily Telegram prompt: 5 Grok-powered topic suggestions
3. User picks topic → 2 post versions + infographic generated → user picks A or B
4. Bot sends a LinkedIn pre-fill URL as an inline button — one tap to post

Slug: "linkedin"
Session state machine: IDLE → TOPIC_SENT → VERSIONS_SENT → COMPLETED | EXPIRED
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.agents.base import BaseAgent
from app.agents.linkedin.post_generator import generate_edited_versions, generate_post_versions
from app.agents.linkedin.research import fetch_topic_suggestions
from app.agents.linkedin.voice_extractor import extract_voice_profile
from app.config import settings
from app.db.connection import get_service_client

logger = logging.getLogger(__name__)

_MAX_STYLE_NOTES = 8  # consolidate with Haiku when this is exceeded


def _extract_style_note(edit_instruction: str) -> str:
    """Use Haiku to distill one compact preference sentence from an edit request."""
    from anthropic import Anthropic
    from app.config import settings

    if not settings.anthropic_api_key:
        return ""

    prompt = (
        f'A LinkedIn ghostwriting user gave this feedback on a post draft: "{edit_instruction}"\n\n'
        "In one short sentence (max 15 words), what does this reveal about their posting preferences?\n"
        'Examples: "Prefers shorter posts under 150 words" / "Dislikes bullet points, wants flowing prose"\n\n'
        "Return ONLY the one sentence, nothing else."
    )
    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=60,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip().rstrip(".")
    except Exception:
        logger.exception("Style note extraction failed")
        return ""


def _add_style_note(memory: dict, note: str) -> dict:
    """Return updated memory dict with the new style note appended.

    If notes exceed _MAX_STYLE_NOTES, consolidates via Haiku to keep memory lean.
    """
    notes: list[str] = list(memory.get("style_notes", []))
    notes.append(note)

    if len(notes) > _MAX_STYLE_NOTES:
        notes = _consolidate_style_notes(notes)

    return {**memory, "style_notes": notes}


def _consolidate_style_notes(notes: list[str]) -> list[str]:
    """Use Haiku to compress many style notes into 5 denser ones."""
    from anthropic import Anthropic
    from app.config import settings

    if not settings.anthropic_api_key:
        return notes[-_MAX_STYLE_NOTES:]

    bullet_list = "\n".join(f"- {n}" for n in notes)
    prompt = (
        "These are style preferences learned from a LinkedIn post user over time:\n\n"
        f"{bullet_list}\n\n"
        "Consolidate these into exactly 5 concise preference statements, removing duplicates "
        "and merging related ones. Each statement max 15 words.\n\n"
        "Return ONLY a JSON array of 5 strings, e.g. [\"pref 1\", \"pref 2\", ...]"
    )
    try:
        import json
        client = Anthropic(api_key=settings.anthropic_api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        start, end = raw.find("["), raw.rfind("]") + 1
        if start >= 0 and end > start:
            consolidated = json.loads(raw[start:end])
            if isinstance(consolidated, list):
                return [str(n) for n in consolidated[:5]]
    except Exception:
        logger.exception("Style note consolidation failed")

    return notes[-_MAX_STYLE_NOTES:]


_ONBOARDING_STEPS = [
    # step 0: field (free text)
    "What's your job title or field?\n\n_(e.g. Head of Sales at AbbVie, Orthopedic Surgeon, Real Estate Broker)_",
    # step 1: audience — reply keyboard
    "Who is your main LinkedIn audience?",
    # step 2: region — reply keyboard
    "Where is your audience based?",
    # step 3: paste posts
    (
        "Now let me learn your voice.\n\n"
        "Paste your last 5–10 LinkedIn posts below — separated by '---', or send them one by one. "
        "Type *done* when finished."
    ),
    # step 4: time preference
    "What time would you like your topic suggestions?\n\n_(Default is 9:00 AM — just type *default*)_",
    # step 5: posting frequency — reply keyboard
    "How often do you want to post on LinkedIn?",
]

_AUDIENCE_OPTIONS = [
    "Business professionals",
    "Executives / C-suite",
    "Investors",
    "Patients / Public",
    "Mixed audience",
]

_REGION_OPTIONS = [
    "UAE / GCC",
    "UK",
    "US / Canada",
    "Europe",
    "Global",
]

_FREQUENCY_OPTIONS = [
    "Every day",
    "Every other day",
    "Twice a week",
    "Once a week",
]

_FREQUENCY_MAP = {
    "every day": "daily",
    "every other day": "every_other_day",
    "twice a week": "twice_a_week",
    "once a week": "once_a_week",
}


class LinkedInGhostwriterAgent(BaseAgent):
    """LinkedIn Ghostwriter — daily AI-powered thought leadership posts."""

    slug = "linkedin"
    personality_prompt = (
        "You are a professional LinkedIn ghostwriter. "
        "You write in the exact voice of your client — never generic, always authentic. "
        "You know what resonates on LinkedIn: clear insights, personal angles, industry relevance. "
        "Your job is to make your client look brilliant without them doing the work."
    )

    def get_intro_message(self, client: dict) -> str:
        name = client.get("name", "")
        first = name.split()[0] if name else "there"
        return (
            f"Hey {first}! I'm your LinkedIn Ghostwriter from Stratus.\n\n"
            f"Every morning I'll send you 5 topic ideas based on what's trending in your industry. "
            f"You pick one, I write 2 versions in your exact voice plus a chic infographic. "
            f"Pick A or B and I'll send you a one-tap link to post it straight to LinkedIn.\n\n"
            f"Let's get you set up — takes about 3 minutes."
        )

    def get_onboarding_question(self, step: int, collected: dict) -> str | None:
        if step >= len(_ONBOARDING_STEPS):
            return None
        return _ONBOARDING_STEPS[step]

    def get_completion_message(self, client: dict, collected: dict) -> str:
        name = client.get("name", "").split()[0] or "there"
        field = collected.get("field", "your field")
        audience = collected.get("audience", "your audience")
        region = collected.get("region", "your region")
        post_time = collected.get("post_time", "09:00")
        freq_raw = collected.get("post_frequency", "daily")
        freq_label = {
            "daily": "every day",
            "every_other_day": "every other day",
            "twice_a_week": "twice a week (Mon & Thu)",
            "once_a_week": "once a week (Monday)",
        }.get(freq_raw, freq_raw)
        return (
            f"You're all set, {name}!\n\n"
            f"Here's what I know about you:\n"
            f"• *Field:* {field}\n"
            f"• *Audience:* {audience}\n"
            f"• *Region:* {region}\n"
            f"• *Posting:* {freq_label} at {post_time}\n\n"
            f"On your scheduled days I'll research what's trending in your world and send "
            f"5 fresh topic ideas. Pick one, I write two versions + an infographic, "
            f"you pick A or B, and I'll give you a one-tap link to post it to LinkedIn.\n\n"
            f"Type *post* any time to write something right now."
        )

    def get_onboarding_keyboard(self, step: int, collected: dict) -> list[str] | None:
        if step == 1:
            return _AUDIENCE_OPTIONS
        if step == 2:
            return _REGION_OPTIONS
        if step == 5:
            return _FREQUENCY_OPTIONS
        return None

    def process_onboarding_answer(self, step: int, answer: str, collected: dict) -> dict:
        updated = dict(collected)
        answer_stripped = answer.strip()

        if step == 0:
            updated["field"] = answer_stripped

        elif step == 1:
            updated["audience"] = answer_stripped

        elif step == 2:
            updated["region"] = answer_stripped

        elif step == 3:
            existing: list[str] = updated.get("pasted_posts", [])
            if answer_stripped.lower() == "done":
                updated["posts_collection_done"] = True
            else:
                chunks = [p.strip() for p in answer_stripped.split("---") if p.strip()]
                updated["pasted_posts"] = existing + (chunks or [answer_stripped])

        elif step == 4:
            if answer_stripped.lower() in ("default", "ok", "yes", "9:00", "9am", "09:00"):
                updated["post_time"] = "09:00"
            else:
                updated["post_time"] = answer_stripped

        elif step == 5:
            freq = _FREQUENCY_MAP.get(answer_stripped.lower(), "daily")
            updated["post_frequency"] = freq

            # Last step — extract voice profile now that all data is collected
            posts: list[str] = updated.get("pasted_posts", [])
            name = updated.get("_client_name", "")
            if posts:
                logger.info("LinkedIn onboarding: extracting voice from %d posts", len(posts))
                profile = extract_voice_profile(posts, name)
                updated["voice_profile"] = profile
                self._save_voice_profile(updated.get("_client_id", ""), profile, len(posts))

        return updated

    async def handle_message(
        self,
        client: dict,
        message: dict,
        memory: dict,
        profile: dict,
    ) -> str:
        """Handle incoming Telegram message based on active session state."""
        text = message.get("text", "").strip()
        client_id = client["id"]

        session = self._get_active_session(client_id)

        if session and session["state"] == "TOPIC_SENT":
            return await self._handle_topic_selection(client, session, text, memory)

        if session and session["state"] == "VERSIONS_SENT":
            return await self._handle_version_selection(client, session, text, memory)

        # No active session — check if they want to trigger a post now
        lower = text.lower()
        if any(kw in lower for kw in ("post", "write", "topic", "content", "linkedin")):
            field = memory.get("field", "your field")
            audience = memory.get("audience", "business professionals")
            region = memory.get("region", "Global")
            suggestions = await fetch_topic_suggestions(field, audience, region)
            if not suggestions:
                suggestions = self._fallback_suggestions(field)

            session_id = self._create_session(client_id, suggestions)
            self._update_session(session_id, {"state": "TOPIC_SENT"})

            lines = ["Here are some topic ideas for your next LinkedIn post:\n"]
            for i, s in enumerate(suggestions[:5], 1):
                lines.append(f"{i}. *{s.get('topic', '')}*")
                if s.get("angle"):
                    lines.append(f"   _{s['angle']}_")
            lines.append("\nReply with a number (1-5) or type your own topic.")
            return "\n".join(lines)

        return (
            "Your daily topic suggestions come automatically each morning. "
            "Type *post* if you want to write something right now, or just wait for tomorrow's brief."
        )

    async def proactive_outreach(
        self,
        client: dict,
        memory: dict,
        profile: dict,
    ) -> str | None:
        """Send daily topic suggestions. Called by the scheduler at configured time."""
        field = memory.get("field")
        if not field:
            logger.info("LinkedIn: no field in memory for client=%s — skipping", client.get("id"))
            return None

        audience = memory.get("audience", "business professionals")
        region = memory.get("region", "Global")

        suggestions = await fetch_topic_suggestions(field, audience, region)
        if not suggestions:
            suggestions = self._fallback_suggestions(field)

        session_id = self._create_session(client["id"], suggestions)
        self._update_session(session_id, {"state": "TOPIC_SENT"})

        lines = ["Good morning! Here are today's LinkedIn topic ideas:\n"]
        for i, s in enumerate(suggestions[:5], 1):
            lines.append(f"{i}. *{s.get('topic', '')}*")
            if s.get("angle"):
                lines.append(f"   _{s['angle']}_")
        lines.append("\nReply with a number (1-5) or type your own topic.")
        return "\n".join(lines)

    # ── Session helpers ───────────────────────────────────────────────────────

    def _get_active_session(self, client_id: str) -> dict | None:
        """Return the most recent TOPIC_SENT or VERSIONS_SENT session, or None if expired."""
        db = get_service_client()
        result = (
            db.table("linkedin_post_sessions")
            .select("*")
            .eq("client_id", client_id)
            .in_("state", ["TOPIC_SENT", "VERSIONS_SENT"])
            .order("created_at", desc=True)
            .limit(1)
            .maybe_single()
            .execute()
        )
        if not result or not result.data:
            return None

        session = result.data
        expires_at = session.get("expires_at")
        if expires_at:
            exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > exp:
                self._update_session(session["id"], {"state": "EXPIRED"})
                return None

        return session

    def _create_session(self, client_id: str, suggestions: list[dict]) -> str:
        db = get_service_client()
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        result = db.table("linkedin_post_sessions").insert({
            "client_id": client_id,
            "grok_suggestions": suggestions,
            "state": "IDLE",
            "expires_at": expires_at,
        }).execute()
        return result.data[0]["id"]

    def _update_session(self, session_id: str, updates: dict) -> None:
        db = get_service_client()
        db.table("linkedin_post_sessions").update({
            **updates,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", session_id).execute()

    # ── Topic selection ───────────────────────────────────────────────────────

    async def _handle_topic_selection(
        self, client: dict, session: dict, text: str, memory: dict
    ) -> str:
        suggestions = session.get("grok_suggestions") or []

        topic = angle = ""
        if text.strip().isdigit() and 1 <= int(text.strip()) <= len(suggestions):
            idx = int(text.strip()) - 1
            topic = suggestions[idx].get("topic", "")
            angle = suggestions[idx].get("angle", "")
        else:
            topic = text.strip()
            angle = ""

        if not topic:
            return "Reply with a number (1-5) or type your own topic."

        await self._send_typing(client)

        name = client.get("name", "")
        voice_profile = memory.get("voice_profile", {})
        style_notes = memory.get("style_notes", [])

        versions = generate_post_versions(topic, angle, name, voice_profile, style_notes)
        if not versions.version_a or not versions.version_b:
            return "Couldn't generate posts right now — try again in a moment."

        self._update_session(session["id"], {
            "topic": topic,
            "version_a": versions.version_a,
            "version_b": versions.version_b,
            "state": "VERSIONS_SENT",
        })

        return (
            f"Here are 2 versions for *{topic}*:\n\n"
            f"— VERSION A —\n{versions.version_a}\n\n"
            f"— — —\n\n"
            f"— VERSION B —\n{versions.version_b}\n\n"
            f"— — —\n\n"
            f"Reply *A* or *B* to post it to LinkedIn.\n"
            f"Or reply *visual* to get an infographic."
        )

    # ── Version selection ─────────────────────────────────────────────────────

    async def _handle_version_selection(
        self, client: dict, session: dict, text: str, memory: dict
    ) -> str:
        choice = text.upper().strip()
        lower = text.lower().strip()

        # Infographic request
        if any(kw in lower for kw in ("visual", "infographic", "image", "graphic", "slide")):
            return await self._handle_infographic_request(client, session, memory)

        # Not A/B → treat as an edit instruction
        if choice not in ("A", "B"):
            return await self._handle_edit_request(client, session, text, memory)

        content = session.get("version_a", "") if choice == "A" else session.get("version_b", "")
        if not content:
            return "Something went wrong — I can't find your post versions. Type *post* to start over."

        chat_id = client.get("telegram_chat_id")
        topic = session.get("topic", "")

        await self._send_typing(client)

        from app.agents.linkedin.infographic import generate_infographic
        from app.agents.linkedin.share_link import build_linkedin_url
        from app.telegram.client import send_photo, send_with_inline_button

        # Generate and send infographic first
        author_name = client.get("name", "")
        author_field = memory.get("field", "")
        img_bytes = await generate_infographic(topic, content, author_name, author_field)
        if img_bytes and chat_id:
            await send_photo(
                chat_id,
                img_bytes,
                caption=f"*{topic}*",
                bot_token=settings.telegram_bot_token_linkedin,
            )

        # Mark session done and send LinkedIn pre-fill link as inline button
        self._update_session(session["id"], {
            "selected_version": choice,
            "state": "COMPLETED",
        })

        share_url = build_linkedin_url(content)
        first = client.get("name", "").split()[0] or "there"

        if chat_id:
            await send_with_inline_button(
                chat_id,
                f"Your post is ready, {first}! Tap below to open LinkedIn with it pre-filled — just hit *Post* and you're live.",
                "Post to LinkedIn ↗",
                share_url,
                bot_token=settings.telegram_bot_token_linkedin,
            )
            return ""

        return f"Here's your LinkedIn post:\n\n{content}\n\nPost it here: {share_url}"

    # ── Infographic ───────────────────────────────────────────────────────────

    async def _handle_infographic_request(
        self, client: dict, session: dict, memory: dict
    ) -> str:
        """Generate a chic infographic from the current post and send it as a photo."""
        topic = session.get("topic", "")
        post_text = session.get("version_a", "")

        if not topic or not post_text:
            return "I don't have a post to turn into an infographic yet. Pick a topic first."

        chat_id = client.get("telegram_chat_id")
        if not chat_id:
            return "Can't find your Telegram chat — please contact support."

        await self._send_typing(client)

        author_name = client.get("name", "")
        author_field = memory.get("field", "")

        from app.agents.linkedin.infographic import generate_infographic
        from app.telegram.client import send_photo

        img_bytes = await generate_infographic(topic, post_text, author_name, author_field)

        if not img_bytes:
            return "Couldn't generate the infographic right now — try again in a moment."

        await send_photo(
            chat_id,
            img_bytes,
            caption=f"*{topic}*\n\nReply *A* or *B* and I'll send you the LinkedIn link.",
            bot_token=settings.telegram_bot_token_linkedin,
        )
        return ""

    # ── Edit / regenerate ─────────────────────────────────────────────────────

    async def _handle_edit_request(
        self, client: dict, session: dict, edit_instruction: str, memory: dict
    ) -> str:
        """Regenerate posts based on user's edit feedback and learn from it."""
        topic = session.get("topic", "")
        version_a = session.get("version_a", "")
        version_b = session.get("version_b", "")

        if not version_a:
            return "Something went wrong — I lost your previous versions. Type *post* to start over."

        await self._send_typing(client)

        name = client.get("name", "")
        voice_profile = memory.get("voice_profile", {})
        style_notes = memory.get("style_notes", [])

        versions = generate_edited_versions(
            topic, edit_instruction, version_a, version_b,
            name, voice_profile, style_notes,
        )

        if not versions.version_a:
            return "Couldn't regenerate right now — try again in a moment."

        self._update_session(session["id"], {
            "version_a": versions.version_a,
            "version_b": versions.version_b,
        })

        # Learn from this edit instruction in background (fire and don't block reply)
        import asyncio
        asyncio.create_task(
            self._learn_from_edit(client["id"], edit_instruction, memory)
        )

        return (
            f"Here are updated versions:\n\n"
            f"— VERSION A —\n{versions.version_a}\n\n"
            f"— — —\n\n"
            f"— VERSION B —\n{versions.version_b}\n\n"
            f"— — —\n\n"
            f"Reply *A* or *B* to post, or keep giving me feedback."
        )

    async def _learn_from_edit(
        self, client_id: str, edit_instruction: str, memory: dict
    ) -> None:
        """Extract a compact style note from the edit and persist it."""
        note = _extract_style_note(edit_instruction)
        if note:
            updated_memory = _add_style_note(memory, note)
            from app.agents.memory import save_agent_memory
            save_agent_memory(client_id, self.slug, updated_memory)
            logger.info("LinkedIn: learned style note for client=%s: %s", client_id, note)

    # ── DB helpers ────────────────────────────────────────────────────────────

    def _save_voice_profile(self, client_id: str, profile: dict, posts_analyzed: int) -> None:
        if not client_id:
            return
        db = get_service_client()
        db.table("voice_profiles").upsert({
            "client_id": client_id,
            "raw_profile": profile,
            "posts_analyzed": posts_analyzed,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="client_id").execute()

    async def _send_typing(self, client: dict) -> None:
        chat_id = client.get("telegram_chat_id")
        if chat_id:
            try:
                from app.config import settings as _settings
                from app.telegram.client import send_typing
                await send_typing(chat_id, bot_token=_settings.telegram_bot_token_linkedin)
            except Exception:
                pass

    # ── Fallback topics ───────────────────────────────────────────────────────

    @staticmethod
    def _fallback_suggestions(industry: str) -> list[dict]:
        return [
            {"topic": f"Lessons from 2025 in {industry}", "angle": "Personal reflection with actionable takeaways"},
            {"topic": f"The biggest misconception about {industry}", "angle": "Contrarian take that challenges assumptions"},
            {"topic": f"What I wish I knew when I started in {industry}", "angle": "Advice for early-career professionals"},
            {"topic": f"3 trends reshaping {industry} right now", "angle": "Forward-looking analysis"},
            {"topic": f"A decision I made in {industry} I'm glad I took", "angle": "Authentic personal story"},
        ]
