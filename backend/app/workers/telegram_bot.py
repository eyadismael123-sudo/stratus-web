"""Stratus Telegram Bot Worker.

Entry point: python -m app.workers.telegram_bot

Handles:
- /start command → onboarding flow
- Text messages → agent routing (post-onboarding) or onboarding continuation
- Morning briefings delivered via the LinkedIn scheduler's job queue

Runs in polling mode — no domain, no nginx, no SSL required for V1.
"""

from __future__ import annotations

import logging
import sys

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.agents import onboarding
from app.agents.linkedin.agent import LinkedInPostAgent
from app.agents.linkedin.scheduler import setup_jobs
from app.agents.memory import load_agent_memory, load_master_profile
from app.agents.registry import get_agent, route_message
from app.config import settings
from app.db.connection import get_service_client

logger = logging.getLogger(__name__)

_linkedin_agent = LinkedInPostAgent()


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _get_client_by_chat_id(chat_id: int) -> dict | None:
    """Look up a client row by their Telegram chat ID."""
    db = get_service_client()
    result = (
        db.table("clients")
        .select("*")
        .eq("telegram_chat_id", str(chat_id))
        .maybe_single()
        .execute()
    )
    if result is not None and result.data:
        return result.data
    return None


def _get_active_agents(client_id: str) -> list[str]:
    """Return agent slugs this client has active."""
    db = get_service_client()
    result = (
        db.table("client_agents")
        .select("agent_slug")
        .eq("client_id", client_id)
        .eq("is_active", True)
        .execute()
    )
    return [row["agent_slug"] for row in (result.data or [])]


# ---------------------------------------------------------------------------
# Onboarding state machine
# ---------------------------------------------------------------------------

async def _handle_onboarding(
    update: Update,
    client: dict,
    agent_slug: str,
    user_text: str | None = None,
) -> None:
    """Drive the onboarding state machine for one agent."""
    agent = get_agent(agent_slug)
    if not agent:
        await update.message.reply_text("Agent not available. Contact support.")
        return

    client_id = client["id"]
    session = onboarding.get_session(client_id, agent_slug)

    # First time — no session yet
    if session is None:
        session = onboarding.start_session(client_id, agent_slug)
        intro = agent.get_intro_message(client)
        await update.message.reply_text(intro)
        first_q = agent.get_onboarding_question(0, {})
        if first_q:
            await update.message.reply_text(first_q)
        return

    # Session exists but user sent something — process it
    if session.get("is_complete"):
        return  # caller should route to handle_message instead

    if user_text is None:
        # Resend the current question
        step = session.get("step", 0)
        collected = session.get("collected_data", {})
        q = agent.get_onboarding_question(step, collected)
        if q:
            await update.message.reply_text(q)
        return

    step = session.get("step", 0)
    collected = session.get("collected_data", {})

    # Pass client_id so agent can persist to linkedin_memory on final step
    collected_with_id = dict(collected)
    collected_with_id["client_id"] = client_id

    updated = agent.process_onboarding_answer(step, user_text, collected_with_id)
    next_step = step + 1

    next_q = agent.get_onboarding_question(next_step, updated)

    if next_q is None:
        # All steps done
        onboarding.advance_step(client_id, agent_slug, next_step, updated, complete=True)
        # Seed Layer 2 memory with onboarding data
        from app.agents.memory import save_agent_memory
        save_agent_memory(client_id, agent_slug, updated)
        await update.message.reply_text(
            "You're all set! ✓\n\n"
            "I'll send you 3 post ideas every morning at "
            f"{updated.get('post_time', '08:00')} your local time.\n\n"
            "You can message me anytime to refine ideas or adjust your preferences."
        )
    else:
        onboarding.advance_step(client_id, agent_slug, next_step, updated)
        await update.message.reply_text(next_q)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start — look up client and begin onboarding or resume session."""
    chat_id = update.effective_chat.id
    client = _get_client_by_chat_id(chat_id)

    if not client:
        await update.message.reply_text(
            "Hey! You're not registered yet.\n\n"
            "Contact Eyad to get set up with Stratus."
        )
        return

    active_agents = _get_active_agents(client["id"])
    if not active_agents:
        await update.message.reply_text(
            f"Hey {client.get('name', '')}! You don't have any agents active yet.\n\n"
            "Contact Eyad to activate your subscription."
        )
        return

    # Check each agent's onboarding status
    for slug in active_agents:
        if not onboarding.is_complete(client["id"], slug):
            await _handle_onboarding(update, client, slug)
            return

    # All agents onboarded
    name = client.get("name", "").split()[0] or "there"
    await update.message.reply_text(
        f"Hey {name}! You're all set up.\n\n"
        "Your morning briefing arrives at 08:00 every day.\n"
        "Message me anytime to refine post ideas or adjust preferences."
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help — brief usage guide."""
    await update.message.reply_text(
        "Stratus LinkedIn Post Agent\n\n"
        "Every morning at 08:00 I send 3 post ideas written in your voice.\n\n"
        "Commands:\n"
        "/start — begin onboarding or check status\n"
        "/help — show this message\n\n"
        "Reply with a number (1, 2, 3) to refine a specific idea.\n"
        "Or just message me naturally — I understand context."
    )


# ---------------------------------------------------------------------------
# Text message handler
# ---------------------------------------------------------------------------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route incoming text to onboarding or agent.handle_message()."""
    chat_id = update.effective_chat.id
    user_text = update.message.text or ""

    client = _get_client_by_chat_id(chat_id)
    if not client:
        await update.message.reply_text(
            "You're not registered. Contact Eyad to get started."
        )
        return

    active_agents = _get_active_agents(client["id"])
    if not active_agents:
        await update.message.reply_text(
            "No active agents on your account. Contact Eyad."
        )
        return

    # Find the first agent that hasn't finished onboarding
    for slug in active_agents:
        if not onboarding.is_complete(client["id"], slug):
            await _handle_onboarding(update, client, slug, user_text=user_text)
            return

    # All onboarded — route to the active agent
    slug = active_agents[0]
    agent = get_agent(slug)
    if not agent:
        await update.message.reply_text("Agent unavailable — try again later.")
        return

    memory = load_agent_memory(client["id"], slug)
    profile = load_master_profile(client["id"])

    reply = await agent.handle_message(
        client=client,
        message={"text": user_text},
        memory=memory,
        profile=profile,
    )

    await update.message.reply_text(reply, disable_web_page_preview=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    token = settings.telegram_bot_token
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set — cannot start bot")
        sys.exit(1)

    application = (
        Application.builder()
        .token(token)
        .build()
    )

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Register the LinkedIn morning briefing scheduler
    setup_jobs(application)

    logger.info("Stratus Telegram bot starting in polling mode")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
