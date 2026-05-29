"""Stratus Telegram Bot Worker.

Entry point: python -m app.workers.telegram_bot

Handles:
- /start command → welcome message (no onboarding — profile set up via Google Form)
- Text messages → agent routing
- Morning briefings delivered via the LinkedIn scheduler's job queue

Runs in polling mode — no domain, no nginx, no SSL required for V1.
"""

from __future__ import annotations

import logging
import sys

from urllib.parse import quote

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.agents.linkedin.agent import LinkedInPostAgent
from app.agents.linkedin.scheduler import setup_jobs
from app.agents.memory import load_agent_memory, load_master_profile
from app.agents.registry import get_agent
from app.config import settings
from app.db.connection import get_service_client

logger = logging.getLogger(__name__)

_linkedin_agent = LinkedInPostAgent()

_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [["💡 New Post Ideas", "✏️ Refine", "🚀 Post to LinkedIn"]],
    resize_keyboard=True,
    is_persistent=True,
)

_LINKEDIN_URL = "https://www.linkedin.com/feed/?shareActive=true&text={text}"


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _get_client_by_chat_id(chat_id: int) -> dict | None:
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
# Command handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    name = client.get("name", "").split()[0] or "there"
    memory = load_agent_memory(client["id"], active_agents[0])
    post_time = memory.get("post_time", "08:00")

    await update.message.reply_text(
        f"Hey {name}! Your LinkedIn Post Agent is active.\n\n"
        f"Every morning at {post_time} I'll send you 3 post ideas written in your voice.\n\n"
        "Use the buttons below anytime.",
        reply_markup=_MENU_KEYBOARD,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Stratus LinkedIn Post Agent\n\n"
        "Every morning I send 3 post ideas written in your voice.\n\n"
        "Commands:\n"
        "/start — check status\n"
        "/help — show this message\n\n"
        "Reply with a number (1, 2, 3) to refine a specific idea.\n"
        "Or just message me naturally — I understand context."
    )


async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    username = update.effective_user.username or ""
    await update.message.reply_text(
        f"Your Telegram chat ID is: {chat_id}\n"
        f"Username: @{username}\n\n"
        "Send this to Eyad to get registered."
    )


# ---------------------------------------------------------------------------
# Text message handler
# ---------------------------------------------------------------------------

async def _send_reply(message, reply) -> None:
    """Send a reply — inline keyboard dict or plain text with persistent menu."""
    if isinstance(reply, dict):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(opt["label"], callback_data=opt["data"])]
            for opt in reply.get("options", [])
        ])
        await message.reply_text(
            reply["text"],
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
    else:
        await message.reply_text(
            str(reply),
            reply_markup=_MENU_KEYBOARD,
            disable_web_page_preview=True,
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_text = update.message.text or ""

    client = _get_client_by_chat_id(chat_id)
    if not client:
        await update.message.reply_text(
            "You're not registered. Contact Eyad to get started.",
            reply_markup=_MENU_KEYBOARD,
        )
        return

    active_agents = _get_active_agents(client["id"])
    if not active_agents:
        await update.message.reply_text(
            "No active agents on your account. Contact Eyad.",
            reply_markup=_MENU_KEYBOARD,
        )
        return

    slug = active_agents[0]

    # "🚀 Post to LinkedIn" persistent keyboard tap — serve URL directly from memory
    if "post to linkedin" in user_text.lower():
        memory = load_agent_memory(client["id"], slug)
        draft = memory.get("current_draft", "")
        if not draft:
            await update.message.reply_text(
                "No draft saved yet — tap 💡 New Post Ideas to get started.",
                reply_markup=_MENU_KEYBOARD,
            )
            return
        url = _LINKEDIN_URL.format(text=quote(draft[:700]))
        await update.message.reply_text(
            f"Ready to post:\n{url}",
            reply_markup=_MENU_KEYBOARD,
            disable_web_page_preview=True,
        )
        return

    agent = get_agent(slug)
    if not agent:
        await update.message.reply_text(
            "Agent unavailable — try again later.",
            reply_markup=_MENU_KEYBOARD,
        )
        return

    memory = load_agent_memory(client["id"], slug)
    profile = load_master_profile(client["id"])

    reply = await agent.handle_message(
        client=client,
        message={"text": user_text},
        memory=memory,
        profile=profile,
    )

    await _send_reply(update.message, reply)


# ---------------------------------------------------------------------------
# Inline keyboard callback handler
# ---------------------------------------------------------------------------

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass  # stale callback queries expire after bot restarts — safe to ignore

    chat_id = query.message.chat.id
    client = _get_client_by_chat_id(chat_id)
    if not client:
        await query.message.reply_text("You're not registered. Contact Eyad to get started.")
        return

    active_agents = _get_active_agents(client["id"])
    if not active_agents:
        await query.message.reply_text("No active agents on your account.")
        return

    slug = active_agents[0]
    agent = get_agent(slug)
    if not agent:
        await query.message.reply_text("Agent unavailable — try again later.")
        return

    memory = load_agent_memory(client["id"], slug)
    profile = load_master_profile(client["id"])

    reply = await agent.handle_callback(
        callback_data=query.data,
        client=client,
        memory=memory,
        profile=profile,
    )

    await _send_reply(query.message, reply)


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
    application.add_handler(CommandHandler("myid", cmd_myid))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(handle_callback_query))

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
