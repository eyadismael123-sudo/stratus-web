"""LinkedIn Ghostwriter Agent.

Telegram-native agent that:
1. Onboards users: LinkedIn OAuth → industry → paste posts → set time
2. Daily Telegram prompt: 5 Grok-powered topic suggestions
3. User picks topic → 2 post versions generated → user picks A or B → posted to LinkedIn

Slug: "linkedin"
Session state machine: IDLE → TOPIC_SENT → VERSIONS_SENT → COMPLETED | EXPIRED
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.agents.base import BaseAgent
from app.agents.linkedin.post_generator import generate_post_versions
from app.agents.linkedin.research import fetch_topic_suggestions
from app.agents.linkedin.voice_extractor import extract_voice_profile
from app.config import settings
from app.db.connection import get_service_client

logger = logging.getLogger(__name__)

_ONBOARDING_STEPS = [
    # step 0: OAuth — special, sends auth link
    None,
    # step 1: industry
    "What industry are you in? (e.g. healthcare, real estate, finance, tech, pharma)",
    # step 2: paste posts
    (
        "Now let me learn your voice.\n\n"
        "Paste your last 5-10 LinkedIn posts below — you can paste them all at once "
        "separated by '---', or send them one by one. "
        "When you're done, type *done*."
    ),
    # step 3: time preference
    "What time would you like your daily topic suggestions? (Default is 9:00 AM. Reply with a time like '8:30' or just 'default')",
]


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
            f"You pick one, I write 2 versions in your exact voice, you pick A or B, "
            f"and I post it to LinkedIn automatically.\n\n"
            f"Let's get you set up — takes about 3 minutes."
        )

    def get_onboarding_question(self, step: int, collected: dict) -> str | None:
        if step >= len(_ONBOARDING_STEPS):
            return None

        if step == 0:
            # Generate OAuth URL and return it as the "question"
            from app.agents.linkedin.oauth import generate_auth_url
            client_id = collected.get("_client_id", "")
            if settings.linkedin_client_id and client_id:
                auth_url, _ = generate_auth_url(client_id)
                return (
                    f"First, connect your LinkedIn account so I can post on your behalf.\n\n"
                    f"Click here to authorize:\n{auth_url}\n\n"
                    f"Once done, type *connected* or send any message to continue."
                )
            return (
                "LinkedIn OAuth isn't configured yet. "
                "Ask your Stratus admin to set it up, then type *skip* to continue."
            )

        return _ONBOARDING_STEPS[step]

    def process_onboarding_answer(self, step: int, answer: str, collected: dict) -> dict:
        updated = dict(collected)
        answer_stripped = answer.strip()

        if step == 0:
            updated["oauth_acknowledged"] = True

        elif step == 1:
            updated["industry"] = answer_stripped

        elif step == 2:
            # Accumulate pasted posts. User may send multiple messages or paste all at once.
            existing: list[str] = updated.get("pasted_posts", [])
            if answer_stripped.lower() == "done":
                updated["posts_collection_done"] = True
            else:
                # Split on "---" separator if pasting many at once
                chunks = [p.strip() for p in answer_stripped.split("---") if p.strip()]
                updated["pasted_posts"] = existing + (chunks or [answer_stripped])

        elif step == 3:
            if answer_stripped.lower() in ("default", "ok", "yes", "9:00", "9am", "09:00"):
                updated["post_time"] = "09:00"
            else:
                updated["post_time"] = answer_stripped

            # Extract voice profile from accumulated posts
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
            return await self._handle_version_selection(client, session, text)

        # No active session — check if they want to trigger a post now
        lower = text.lower()
        if any(kw in lower for kw in ("post", "write", "topic", "content", "linkedin")):
            industry = memory.get("industry", "your industry")
            suggestions = await fetch_topic_suggestions(industry)
            if not suggestions:
                suggestions = self._fallback_suggestions(industry)

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
        industry = memory.get("industry")
        if not industry:
            logger.info("LinkedIn: no industry for client=%s — skipping", client.get("id"))
            return None

        suggestions = await fetch_topic_suggestions(industry)
        if not suggestions:
            suggestions = self._fallback_suggestions(industry)

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

        versions = generate_post_versions(topic, angle, name, voice_profile)
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
            f"Reply *A* or *B* to post it to LinkedIn."
        )

    # ── Version selection ─────────────────────────────────────────────────────

    async def _handle_version_selection(
        self, client: dict, session: dict, text: str
    ) -> str:
        choice = text.upper().strip()

        if choice == "A":
            content = session.get("version_a", "")
        elif choice == "B":
            content = session.get("version_b", "")
        else:
            return "Please reply *A* or *B* to choose which version to post."

        if not content:
            return "Something went wrong — I can't find your post versions. Type *post* to start over."

        client_id = client["id"]
        linkedin_account = self._get_linkedin_account(client_id)

        if not linkedin_account:
            return (
                "Your LinkedIn account isn't connected. "
                "Visit stratus.ai/dashboard to reconnect."
            )

        try:
            from app.agents.linkedin.linkedin_api import create_post
            from app.agents.linkedin.oauth import refresh_access_token

            access_token = linkedin_account["access_token"]
            expires_at_str = linkedin_account.get("token_expires_at", "")

            if expires_at_str:
                exp = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) > exp - timedelta(minutes=5):
                    rt = linkedin_account.get("refresh_token")
                    if rt:
                        refreshed = refresh_access_token(rt)
                        access_token = refreshed["access_token"]
                        self._save_tokens(client_id, refreshed)

            result = create_post(
                access_token,
                linkedin_account["linkedin_user_id"],
                content,
            )
            post_urn = result.get("post_urn", "")

            self._record_post(client_id, session["id"], session.get("topic", ""), content, post_urn)
            self._update_session(session["id"], {
                "selected_version": choice,
                "linkedin_post_id": post_urn,
                "posted_at": datetime.now(timezone.utc).isoformat(),
                "state": "COMPLETED",
            })

            first = client.get("name", "").split()[0] or "Done"
            return (
                f"Posted to LinkedIn, {first}!\n\n"
                f"I'll send tomorrow's topic ideas at the same time."
            )

        except Exception:
            logger.exception("LinkedIn post failed for client=%s", client_id)
            return "Couldn't post to LinkedIn right now. Check your account connection at stratus.ai/dashboard."

    # ── DB helpers ────────────────────────────────────────────────────────────

    def _get_linkedin_account(self, client_id: str) -> dict | None:
        db = get_service_client()
        result = (
            db.table("linkedin_accounts")
            .select("*")
            .eq("client_id", client_id)
            .eq("is_active", True)
            .maybe_single()
            .execute()
        )
        return result.data if result else None

    def _save_tokens(self, client_id: str, token_data: dict) -> None:
        db = get_service_client()
        db.table("linkedin_accounts").update({
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "token_expires_at": token_data.get("expires_at"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("client_id", client_id).execute()

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

    def _record_post(
        self,
        client_id: str,
        session_id: str,
        topic: str,
        content: str,
        linkedin_post_id: str,
    ) -> None:
        db = get_service_client()
        db.table("linkedin_posts").insert({
            "client_id": client_id,
            "session_id": session_id,
            "topic": topic,
            "content": content,
            "linkedin_post_id": linkedin_post_id,
        }).execute()

    async def _send_typing(self, client: dict) -> None:
        chat_id = client.get("telegram_chat_id")
        if chat_id:
            try:
                from app.telegram.client import send_typing
                await send_typing(chat_id)
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
