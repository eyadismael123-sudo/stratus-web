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


def _base_url(bot_token: str) -> str:
    return f"https://api.telegram.org/bot{bot_token}"


def _resolve_token(bot_token: str) -> str:
    """Return bot_token if provided, else fall back to legacy TELEGRAM_BOT_TOKEN."""
    return bot_token or settings.telegram_bot_token


async def send_typing(chat_id: int | str, bot_token: str = "") -> None:
    """Show 'typing...' indicator to the user."""
    token = _resolve_token(bot_token)
    if not token:
        return
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{_base_url(token)}/sendChatAction",
                json={"chat_id": chat_id, "action": "typing"},
                timeout=5.0,
            )
        except Exception:
            logger.exception("Failed to send typing action to chat_id=%s", chat_id)


async def send_text(
    chat_id: int | str,
    text: str,
    parse_mode: str = "Markdown",
    bot_token: str = "",
) -> dict | None:
    """Send a text message. Returns Telegram's response dict."""
    token = _resolve_token(bot_token)
    if not token:
        logger.warning("No Telegram bot token — printing to stdout instead")
        print(f"\n[Telegram → {chat_id}]\n{text}\n{'─'*60}\n")
        return None

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{_base_url(token)}/sendMessage",
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


async def send_with_keyboard(
    chat_id: int | str,
    text: str,
    options: list[str],
    row_size: int = 2,
    bot_token: str = "",
) -> dict | None:
    """Send a message with a reply keyboard showing button options.

    Buttons disappear after the user taps one (one_time_keyboard=True).
    """
    token = _resolve_token(bot_token)
    if not token:
        print(f"\n[Telegram → {chat_id}]\n{text}\nOptions: {options}\n{'─'*60}\n")
        return None

    rows = [options[i:i + row_size] for i in range(0, len(options), row_size)]
    reply_markup = {
        "keyboard": [[{"text": opt} for opt in row] for row in rows],
        "one_time_keyboard": True,
        "resize_keyboard": True,
    }

    await send_typing(chat_id, bot_token=token)
    delay = _typing_delay(text)
    await asyncio.sleep(delay)

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{_base_url(token)}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "reply_markup": reply_markup,
                    "disable_web_page_preview": True,
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            logger.exception("Failed to send keyboard message to chat_id=%s", chat_id)
            return None


async def send_with_human_feel(
    chat_id: int | str,
    text: str,
    bot_token: str = "",
) -> dict | None:
    """Send with human-feel: show typing → delay → send."""
    await send_typing(chat_id, bot_token=bot_token)
    delay = _typing_delay(text)
    logger.debug("Human-feel delay: %.1fs for %d words", delay, len(text.split()))
    await asyncio.sleep(delay)
    return await send_text(chat_id, text, bot_token=bot_token)


async def send_with_inline_button(
    chat_id: int | str,
    text: str,
    button_label: str,
    url: str,
    bot_token: str = "",
) -> dict | None:
    """Send a message with a single inline URL button."""
    token = _resolve_token(bot_token)
    if not token:
        print(f"\n[Telegram → {chat_id}]\n{text}\nButton: {button_label} → {url}\n{'─'*60}\n")
        return None

    reply_markup = {"inline_keyboard": [[{"text": button_label, "url": url}]]}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{_base_url(token)}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "reply_markup": reply_markup,
                    "disable_web_page_preview": True,
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            logger.exception("Failed to send inline button message to chat_id=%s", chat_id)
            return None


async def send_photo(
    chat_id: int | str,
    photo_bytes: bytes,
    caption: str = "",
    bot_token: str = "",
) -> dict | None:
    """Upload and send a PNG/JPEG photo to a Telegram chat."""
    token = _resolve_token(bot_token)
    if not token:
        logger.warning("No Telegram bot token — cannot send photo to chat_id=%s", chat_id)
        return None

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{_base_url(token)}/sendPhoto",
                data={
                    "chat_id": str(chat_id),
                    "caption": caption,
                    "parse_mode": "Markdown",
                },
                files={"photo": ("infographic.png", photo_bytes, "image/png")},
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            logger.exception("Failed to send photo to chat_id=%s", chat_id)
            return None
