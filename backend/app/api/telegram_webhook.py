"""Telegram webhook endpoints — one per bot.

Routes:
  POST /webhook/telegram/brief    → @stratusDebriefBot   → Brief agent
  POST /webhook/telegram/linkedin → @stratuslinkedinbot  → LinkedIn agent

Each route is hardcoded to its agent slug and uses its own bot token,
so there is zero routing ambiguity between agents.

Webhook registration (run once per bot after deploy):
  curl -X POST https://api.telegram.org/bot<TOKEN>/setWebhook \
       -d '{"url": "https://your-domain.com/webhook/telegram/<agent>"}'
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Request

from app.agents import memory as mem_store
from app.agents import onboarding as ob_store
from app.agents.registry import get_agent, get_client_agents, route_message
from app.config import settings
from app.db.connection import get_service_client
from app.telegram.client import send_with_human_feel, send_with_keyboard

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["telegram"])

# ── Bot token map ─────────────────────────────────────────────────────────────

_BOT_TOKENS: dict[str, str] = {}


def _token(agent_slug: str) -> str:
    """Resolve bot token for an agent slug at request time (settings are loaded by then)."""
    if agent_slug == "brief":
        return settings.telegram_bot_token_brief or settings.telegram_bot_token
    if agent_slug == "linkedin":
        return settings.telegram_bot_token_linkedin
    return settings.telegram_bot_token


# ── Client lookup ─────────────────────────────────────────────────────────────


def _get_client_by_telegram(chat_id: str, username: str | None = None) -> dict | None:
    """Look up client by chat_id first; fall back to @username for first-contact matching."""
    db = get_service_client()

    result = (
        db.table("clients")
        .select("*")
        .eq("telegram_chat_id", chat_id)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    if result.data:
        return result.data

    if username:
        result = (
            db.table("clients")
            .select("*")
            .eq("telegram_username", username)
            .eq("is_active", True)
            .maybe_single()
            .execute()
        )
        return result.data

    return None


def _sync_telegram_identity(client_id: str, chat_id: str, username: str | None) -> None:
    """Persist chat_id and username on the client row so outbound messages always work."""
    db = get_service_client()
    update: dict = {"telegram_chat_id": chat_id}
    if username:
        update["telegram_username"] = username
    try:
        db.table("clients").update(update).eq("id", client_id).execute()
    except Exception:
        logger.exception("Failed to sync Telegram identity for client=%s", client_id)


# ── Onboarding handler ────────────────────────────────────────────────────────


async def _handle_onboarding(
    client: dict,
    agent_slug: str,
    incoming_text: str,
    bot_token: str,
) -> None:
    agent = get_agent(agent_slug)
    if not agent:
        return

    chat_id = client["telegram_chat_id"]
    session = ob_store.get_session(client["id"], agent_slug)

    if session is None:
        ob_store.start_session(client["id"], agent_slug)
        intro = agent.get_intro_message(client)
        await send_with_human_feel(chat_id, intro, bot_token=bot_token)

        first_q = agent.get_onboarding_question(0, {})
        if first_q:
            await send_with_human_feel(chat_id, first_q, bot_token=bot_token)
        return

    step = session.get("step", 0)
    collected = session.get("collected_data") or {}

    updated_collected = agent.process_onboarding_answer(
        step,
        incoming_text,
        {**collected, "_client_id": client["id"], "_client_name": client.get("name", "")},
    )
    next_step = step + 1
    next_q = agent.get_onboarding_question(next_step, updated_collected)

    if next_q is None:
        ob_store.advance_step(client["id"], agent_slug, next_step, updated_collected, complete=True)
        mem_store.save_agent_memory(client["id"], agent_slug, updated_collected)

        completion_msg = agent.get_completion_message(client, updated_collected)
        await send_with_human_feel(chat_id, completion_msg, bot_token=bot_token)
    else:
        ob_store.advance_step(client["id"], agent_slug, next_step, updated_collected)
        keyboard = agent.get_onboarding_keyboard(next_step, updated_collected)
        if keyboard:
            await send_with_keyboard(chat_id, next_q, keyboard, bot_token=bot_token)
        else:
            await send_with_human_feel(chat_id, next_q, bot_token=bot_token)


# ── Core update processor ─────────────────────────────────────────────────────


async def _process_update(message: dict, agent_slug: str, bot_token: str) -> None:
    """Process a single incoming Telegram message for a specific agent."""
    chat = message.get("chat", {})
    from_user = message.get("from", {})
    chat_id = str(chat.get("id", ""))
    username = from_user.get("username") or None
    text = message.get("text", "").strip()

    if not chat_id or "text" not in message or not text:
        logger.info("Skipping non-text Telegram update from chat_id=%s", chat_id)
        return

    logger.info("Incoming Telegram [%s] from chat_id=%s username=%s", agent_slug, chat_id, username)

    client = _get_client_by_telegram(chat_id, username)
    if not client:
        logger.info("Unknown chat_id=%s on %s bot", chat_id, agent_slug)
        await send_with_human_feel(
            chat_id,
            "Hi! I'm from Stratus. To get started, contact us at stratus.ai to set up your agent.",
            bot_token=bot_token,
        )
        return

    client_id = client["id"]

    # Keep chat_id and username current — handles first-contact and ID changes
    if client.get("telegram_chat_id") != chat_id or (username and client.get("telegram_username") != username):
        _sync_telegram_identity(client_id, chat_id, username)

    # Verify client has this agent hired
    hired_slugs = get_client_agents(client_id)
    if agent_slug not in hired_slugs:
        await send_with_human_feel(
            chat_id,
            "Your Stratus subscription isn't active yet.\n\nVisit stratus.ai/marketplace to get started.",
            bot_token=bot_token,
        )
        return

    msg_type = "text"
    mem_store.log_message(
        client_id=client_id,
        agent_slug=agent_slug,
        direction="in",
        message_type=msg_type,
        raw_content=text,
    )

    if not ob_store.is_complete(client_id, agent_slug):
        await _handle_onboarding(client, agent_slug, text, bot_token)
        return

    memory = mem_store.load_agent_memory(client_id, agent_slug)
    profile = mem_store.load_master_profile(client_id)

    agent = route_message(client_id, agent_slug)
    if not agent:
        return

    message_dict = {"type": msg_type, "text": text}
    reply = await agent.handle_message(client, message_dict, memory, profile)

    mem_store.log_message(
        client_id=client_id,
        agent_slug=agent_slug,
        direction="out",
        message_type="text",
        raw_content="",
        response=reply,
    )

    await send_with_human_feel(chat_id, reply, bot_token=bot_token)


# ── Webhook endpoints ─────────────────────────────────────────────────────────


@router.post("/telegram/brief")
async def telegram_brief_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive updates from @stratusDebriefBot → Brief agent."""
    body = await request.json()
    message = body.get("message") or body.get("edited_message")
    if message:
        background_tasks.add_task(
            _process_update, message, "brief", _token("brief")
        )
    return {"ok": True}


@router.post("/telegram/linkedin")
async def telegram_linkedin_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive updates from @stratuslinkedinbot → LinkedIn agent."""
    body = await request.json()
    message = body.get("message") or body.get("edited_message")
    if message:
        background_tasks.add_task(
            _process_update, message, "linkedin", _token("linkedin")
        )
    return {"ok": True}
