"""APScheduler cron for LinkedIn Ghostwriter daily topic prompts.

Checks every minute if any LinkedIn client is due for their morning
topic suggestions, then sends via Telegram.
"""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.agents.linkedin.agent import LinkedInGhostwriterAgent
from app.agents.memory import load_agent_memory, load_master_profile
from app.db.connection import get_service_client

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None
_agent = LinkedInGhostwriterAgent()


def _get_active_linkedin_clients() -> list[dict]:
    """Fetch all clients with an active LinkedIn subscription."""
    db = get_service_client()
    result = (
        db.table("client_agents")
        .select("client_id, clients(id, telegram_chat_id, name, timezone)")
        .eq("agent_slug", "linkedin")
        .eq("is_active", True)
        .execute()
    )
    clients = []
    for row in result.data or []:
        client_data = row.get("clients") or {}
        if client_data:
            clients.append(client_data)
    return clients


def _local_time_matches(timezone_str: str, target_hour: int, target_minute: int) -> bool:
    try:
        tz = ZoneInfo(timezone_str)
    except (ZoneInfoNotFoundError, Exception):
        tz = ZoneInfo("Asia/Dubai")
    now = datetime.now(tz)
    return now.hour == target_hour and now.minute == target_minute


def _parse_time(time_str: str) -> tuple[int, int]:
    try:
        parts = time_str.strip().split(":")
        return int(parts[0]), int(parts[1])
    except Exception:
        return 9, 0


def _should_send_today(frequency: str, timezone_str: str) -> bool:
    """Return True if the client's posting frequency calls for a send today."""
    try:
        tz = ZoneInfo(timezone_str)
    except (ZoneInfoNotFoundError, Exception):
        tz = ZoneInfo("Asia/Dubai")

    now = datetime.now(tz)
    weekday = now.weekday()   # 0=Mon … 6=Sun
    day_of_year = now.timetuple().tm_yday

    if frequency == "daily":
        return True
    if frequency == "every_other_day":
        return day_of_year % 2 == 0   # deterministic, ~every 48 h
    if frequency == "twice_a_week":
        return weekday in (0, 3)      # Monday + Thursday
    if frequency == "once_a_week":
        return weekday == 0           # Monday
    return True  # unknown → default daily


async def _run_topic_check() -> None:
    """Send topic suggestions to clients whose configured time has come."""
    clients = _get_active_linkedin_clients()
    if not clients:
        return

    for client in clients:
        client_id = client.get("id")
        timezone_str = client.get("timezone", "Asia/Dubai")
        telegram_chat_id = client.get("telegram_chat_id")

        if not telegram_chat_id:
            continue

        memory = load_agent_memory(client_id, "linkedin")
        post_time = memory.get("post_time", "09:00")
        target_hour, target_minute = _parse_time(post_time)

        if not _local_time_matches(timezone_str, target_hour, target_minute):
            continue

        frequency = memory.get("post_frequency", "daily")
        if not _should_send_today(frequency, timezone_str):
            logger.info(
                "LinkedIn scheduler: skipping client=%s today (frequency=%s)", client_id, frequency
            )
            continue

        logger.info("LinkedIn scheduler: sending topics to client=%s", client_id)

        try:
            profile = load_master_profile(client_id)
            msg = await _agent.proactive_outreach(client, memory, profile)
            if msg:
                from app.config import settings as _settings
                from app.telegram.client import send_with_human_feel
                await send_with_human_feel(
                    telegram_chat_id, msg,
                    bot_token=_settings.telegram_bot_token_linkedin,
                )
                logger.info("LinkedIn: topics delivered to client=%s", client_id)

        except Exception:
            logger.exception("LinkedIn: topic delivery failed for client=%s", client_id)


def start_linkedin_scheduler() -> None:
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _run_topic_check,
        trigger="cron",
        minute="*",
        id="linkedin_topic_check",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info("LinkedIn scheduler started — checking every minute for due topic sends")


def stop_linkedin_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("LinkedIn scheduler stopped")
