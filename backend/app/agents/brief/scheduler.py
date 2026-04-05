"""APScheduler cron for Brief morning briefings.

Sends briefings to each active Brief client at their configured peak_reading_time
(default 06:30) in their local timezone.

The scheduler runs a single cron job every minute and checks which clients
are due for their briefing, rather than creating per-client jobs (which
wouldn't survive restarts without persistence). This keeps it stateless
and restart-safe.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.agents.brief.agent import DoctorBriefAgent
from app.agents.memory import load_agent_memory, load_master_profile
from app.db.connection import get_service_client
from app.whatsapp.client import send_with_human_feel

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None
_agent = DoctorBriefAgent()


def _get_active_brief_clients() -> list[dict]:
    """Fetch all clients with an active Brief subscription."""
    db = get_service_client()
    result = (
        db.table("client_agents")
        .select("client_id, clients(id, whatsapp_number, name, timezone)")
        .eq("agent_slug", "brief")
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
    """Return True if it's currently within the target minute window for this timezone."""
    try:
        tz = ZoneInfo(timezone_str)
    except (ZoneInfoNotFoundError, Exception):
        tz = ZoneInfo("Asia/Dubai")

    now = datetime.now(tz)
    return now.hour == target_hour and now.minute == target_minute


def _parse_peak_time(peak_reading_time: str) -> tuple[int, int]:
    """Parse 'HH:MM' string into (hour, minute). Defaults to (6, 30)."""
    try:
        parts = peak_reading_time.strip().split(":")
        return int(parts[0]), int(parts[1])
    except Exception:
        return 6, 30


async def _run_briefing_check() -> None:
    """Check all active Brief clients and send briefings if it's their time."""
    clients = _get_active_brief_clients()
    if not clients:
        return

    for client in clients:
        client_id = client.get("id")
        timezone_str = client.get("timezone", "Asia/Dubai")
        whatsapp_number = client.get("whatsapp_number")

        if not whatsapp_number:
            continue

        memory = load_agent_memory(client_id, "brief")
        peak_time = memory.get("peak_reading_time", "06:30")
        target_hour, target_minute = _parse_peak_time(peak_time)

        if not _local_time_matches(timezone_str, target_hour, target_minute):
            continue

        logger.info("Brief scheduler: sending briefing to client=%s", client_id)

        try:
            profile = load_master_profile(client_id)
            briefing = await _agent.proactive_outreach(client, memory, profile)

            if briefing:
                await send_with_human_feel(whatsapp_number, briefing)
                logger.info("Brief: briefing delivered to client=%s", client_id)
            else:
                logger.info("Brief: no briefing generated for client=%s", client_id)

        except Exception:
            logger.exception("Brief: briefing failed for client=%s", client_id)


def start_scheduler() -> None:
    """Start the APScheduler background scheduler."""
    global _scheduler

    _scheduler = AsyncIOScheduler()
    # Check every minute — each job checks if it's the client's time
    _scheduler.add_job(
        _run_briefing_check,
        trigger="cron",
        minute="*",  # every minute
        id="brief_briefing_check",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info("Brief scheduler started — checking every minute for due briefings")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Brief scheduler stopped")
