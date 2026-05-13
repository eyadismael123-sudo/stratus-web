"""Telegram webhook endpoint for the Brief doctor agent.

Handles:
- POST /webhook/telegram — Incoming updates from Telegram

Processing flow:
  1. Parse update: get chat_id, text, user info
  2. If not a registered client → send "contact Stratus" response
  3. Check onboarding status — if incomplete, continue onboarding
  4. Route to correct agent via AGENT_REGISTRY
  5. Load memory + master profile
  6. Agent processes → generates response
  7. Human-feel send: typing action → delay → send
  8. Log to agent_logs

Telegram webhook registration:
  POST https://api.telegram.org/bot{TOKEN}/setWebhook
  {"url": "https://your-domain.com/webhook/telegram"}
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Request

from app.agents import memory as mem_store
from app.agents import onboarding as ob_store
from app.agents.registry import route_message
from app.db.connection import get_service_client
from app.telegram.client import send_with_human_feel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["telegram"])


# ─── Client lookup ────────────────────────────────────────────────────────────


def _get_client_by_telegram(telegram_chat_id: str) -> dict | None:
    """Look up a client by Telegram chat_id."""
    db = get_service_client()
    result = (
        db.table("clients")
        .select("*")
        .eq("telegram_chat_id", telegram_chat_id)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    return result.data


# ─── Onboarding handler ───────────────────────────────────────────────────────


async def _handle_onboarding(
    client: dict,
    agent_slug: str,
    incoming_text: str,
) -> None:
    """Drive the onboarding state machine for a client+agent."""
    from app.agents.registry import get_agent
    agent = get_agent(agent_slug)
    if not agent:
        return

    chat_id = client["telegram_chat_id"]
    session = ob_store.get_session(client["id"], agent_slug)

    if session is None:
        ob_store.start_session(client["id"], agent_slug)
        intro = agent.get_intro_message(client)
        await send_with_human_feel(chat_id, intro)

        first_q = agent.get_onboarding_question(0, {})
        if first_q:
            await send_with_human_feel(chat_id, first_q)
        return

    step = session.get("step", 0)
    collected = session.get("collected_data") or {}

    updated_collected = agent.process_onboarding_answer(step, incoming_text, collected)
    next_step = step + 1
    next_q = agent.get_onboarding_question(next_step, updated_collected)

    if next_q is None:
        # Onboarding complete
        ob_store.advance_step(client["id"], agent_slug, next_step, updated_collected, complete=True)
        mem_store.save_agent_memory(client["id"], agent_slug, updated_collected)

        peak = updated_collected.get("peak_reading_time", "06:30")
        name = client.get("name", "Doctor")
        focuses = ", ".join(updated_collected.get("clinical_focus", [])[:2])
        journals = ", ".join(updated_collected.get("trusted_journals", [])[:2])

        completion_msg = (
            f"You're all set, Dr. {name.split()[-1]}.\n\n"
            f"Your first briefing arrives at *{peak}* tomorrow morning. "
            f"I'll cover {focuses} from {journals} and beyond.\n\n"
            f"Any questions before then? Just message me."
        )
        await send_with_human_feel(chat_id, completion_msg)
    else:
        ob_store.advance_step(client["id"], agent_slug, next_step, updated_collected)
        await send_with_human_feel(chat_id, next_q)


# ─── Webhook endpoint ─────────────────────────────────────────────────────────


@router.post("/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive incoming Telegram updates."""
    body = await request.json()

    message = body.get("message") or body.get("edited_message")
    if not message:
        # Could be a callback_query or other update type — ignore for now
        return {"ok": True}

    background_tasks.add_task(_process_update, message)

    # Telegram requires a 200 immediately
    return {"ok": True}


async def _process_update(message: dict) -> None:
    """Process a single incoming Telegram message."""
    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    msg_type = "text" if "text" in message else "other"
    text = message.get("text", "").strip()

    if not chat_id or msg_type != "text" or not text:
        logger.info("Skipping non-text Telegram update from chat_id=%s", chat_id)
        return

    logger.info("Incoming Telegram from chat_id=%s", chat_id)

    # Look up client
    client = _get_client_by_telegram(chat_id)
    if not client:
        logger.info("Unknown chat_id=%s — sending intro response", chat_id)
        await send_with_human_feel(
            chat_id,
            "Hi! I'm *Brief* from Stratus. To get started, contact us at stratus.ai to set up your agent.",
        )
        return

    client_id = client["id"]

    from app.agents.registry import get_client_agents
    hired_slugs = get_client_agents(client_id)

    if not hired_slugs:
        await send_with_human_feel(
            chat_id,
            (
                "Your Stratus subscription isn't active yet.\n\n"
                "To get started with the LinkedIn Ghostwriter, "
                "visit stratus.ai/marketplace or contact your Stratus admin."
            ),
        )
        return

    agent_slug = hired_slugs[0]

    # Log incoming
    mem_store.log_message(
        client_id=client_id,
        agent_slug=agent_slug,
        direction="in",
        message_type=msg_type,
        raw_content=text,
    )

    # Onboarding check
    if not ob_store.is_complete(client_id, agent_slug):
        await _handle_onboarding(client, agent_slug, text)
        return

    # Normal message handling
    memory = mem_store.load_agent_memory(client_id, agent_slug)
    profile = mem_store.load_master_profile(client_id)

    agent = route_message(client_id, agent_slug)
    if not agent:
        return

    message_dict = {"type": msg_type, "text": text}
    reply = await agent.handle_message(client, message_dict, memory, profile)

    # Log outgoing
    mem_store.log_message(
        client_id=client_id,
        agent_slug=agent_slug,
        direction="out",
        message_type="text",
        raw_content="",
        response=reply,
    )

    await send_with_human_feel(chat_id, reply)
