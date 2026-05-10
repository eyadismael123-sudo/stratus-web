"""Telegram Bot API client.

Handles all outbound communication to Telegram:
- Sending text messages (Markdown supported)
- Sending typing action (shows "typing..." indicator)
- Human-feel delay before every send

All sends go through send_with_human_feel() which simulates natural
typing speed.
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_MIN_DELAY = 1.2  # seconds
_MAX_DELAY = 4.5  # seconds
_WPM = 40         # simulated typing speed


def _typing_delay(text: str) -> float:
    words = len(text.split())
    delay = (words / _WPM) * 60
    return max(_MIN_DELAY, min(_MAX_DELAY, delay))


def _base_url() -> str:
    return f"https://api.telegram.org/bot{settings.telegram_bot_token}"


async def send_typing(chat_id: int | str) -> None:
    """Show 'typing...' indicator to the user."""
    if not settings.telegram_bot_token:
        return
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{_base_url()}/sendChatAction",
                json={"chat_id": chat_id, "action": "typing"},
                timeout=5.0,
            )
        except Exception:
            logger.exception("Failed to send typing action to chat_id=%s", chat_id)


async def send_text(chat_id: int | str, text: str, parse_mode: str = "Markdown") -> dict | None:
    """Send a text message. Returns Telegram's response dict."""
    if not settings.telegram_bot_token:
        logger.warning("No TELEGRAM_BOT_TOKEN — printing to stdout instead")
        print(f"\n[Telegram → {chat_id}]\n{text}\n{'─'*60}\n")
        return None

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{_base_url()}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True,
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            logger.exception("Failed to send Telegram message to chat_id=%s", chat_id)
            return None


async def send_with_human_feel(chat_id: int | str, text: str) -> dict | None:
    """Send with human-feel: show typing → delay → send."""
    await send_typing(chat_id)
    delay = _typing_delay(text)
    logger.debug("Human-feel delay: %.1fs for %d words", delay, len(text.split()))
    await asyncio.sleep(delay)
    return await send_text(chat_id, text)
