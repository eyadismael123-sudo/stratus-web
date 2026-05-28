"""Scheduler setup for the LinkedIn Post Agent — Telegram delivery.

Registers a repeating job on the PTB Application's JobQueue.
The job fires every minute and sends briefings to clients whose
local 08:00 window has arrived.
"""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from telegram.ext import Application

from app.agents.linkedin.agent import LinkedInPostAgent
from app.agents.memory import load_agent_memory, load_master_profile
from app.db.connection import get_service_client

logger = logging.getLogger(__name__)

_agent = LinkedInPostAgent()


def _get_active_linkedin_clients() -> list[dict]:
    """Fetch all clients with an active LinkedIn subscription."""
    db = get_service_client()
    result = (
        db.table("client_agents")
        .select("client_id, clients(id, name, timezone, telegram_chat_id)")
        .eq("agent_slug", "linkedin")
        .eq("is_active", True)
        .execute()
    )
    clients = []
    for row in result.data or []:
        client_data = row.get("clients") or {}
        if client_data and client_data.get("telegram_chat_id"):
            clients.append(client_data)
    return clients


def _local_time_matches(timezone_str: str, target_hour: int, target_minute: int) -> bool:
    try:
        tz = ZoneInfo(timezone_str)
    except (ZoneInfoNotFoundError, Exception):
        tz = ZoneInfo("Asia/Dubai")
    now = datetime.now(tz)
    return now.hour == target_hour and now.minute == target_minute


def _parse_post_time(post_time: str) -> tuple[int, int]:
    try:
        parts = post_time.strip().split(":")
        return int(parts[0]), int(parts[1])
    except Exception:
        return 8, 0


async def _briefing_check(context) -> None:
    """Check all active LinkedIn clients and send briefings if it's their time."""
    clients = _get_active_linkedin_clients()
    if not clients:
        return

    for client in clients:
        client_id = client.get("id")
        chat_id = client.get("telegram_chat_id")
        timezone_str = client.get("timezone", "Asia/Dubai")

        memory = load_agent_memory(client_id, "linkedin")
        post_time = memory.get("post_time", "08:00")
        target_hour, target_minute = _parse_post_time(post_time)

        if not _local_time_matches(timezone_str, target_hour, target_minute):
            continue

        logger.info("LinkedIn scheduler: sending briefing to client=%s", client_id)

        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            profile = load_master_profile(client_id)
            briefing = await _agent.proactive_outreach(client, memory, profile)

            if not briefing:
                logger.info("LinkedIn: no briefing generated for client=%s", client_id)
                continue

            if isinstance(briefing, dict):
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(opt["label"], callback_data=opt["data"])]
                    for opt in briefing.get("options", [])
                ])
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=briefing["text"],
                    reply_markup=keyboard,
                    disable_web_page_preview=True,
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=briefing,
                    disable_web_page_preview=True,
                )
            logger.info("LinkedIn: briefing delivered to client=%s", client_id)

        except Exception:
            logger.exception("LinkedIn: briefing failed for client=%s", client_id)


def setup_jobs(application: Application) -> None:
    """Register the briefing check job on the PTB application's job queue."""
    application.job_queue.run_repeating(
        _briefing_check,
        interval=60,   # every minute
        first=10,      # first run 10s after startup
        name="linkedin_briefing_check",
    )
    logger.info("LinkedIn scheduler registered — checking every minute for due briefings")
