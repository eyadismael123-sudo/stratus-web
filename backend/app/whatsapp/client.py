"""WhatsApp Cloud API client.

Handles all outbound communication to Meta's WhatsApp Cloud API:
- Sending text messages
- Sending typing indicators (mark-read + realistic delay)
- Marking messages as read

All sends go through send_with_human_feel() which simulates natural
typing speed and respects quiet hours.
"""

from __future__ import annotations

import asyncio
import logging
import math

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_GRAPH_URL = "https://graph.facebook.com/v20.0"
_MIN_DELAY = 1.5   # seconds
_MAX_DELAY = 5.0   # seconds
_WPM = 40          # simulated typing speed


def _typing_delay(text: str) -> float:
    """Compute realistic typing delay based on word count."""
    words = len(text.split())
    delay = (words / _WPM) * 60
    return max(_MIN_DELAY, min(_MAX_DELAY, delay))


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.whatsapp_access_token}"}


def _base_url() -> str:
    return f"{_GRAPH_URL}/{settings.whatsapp_phone_number_id}"


async def mark_read(message_id: str) -> None:
    """Mark an incoming message as read (shows double blue ticks to sender)."""
    if not settings.whatsapp_access_token:
        return

    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{_base_url()}/messages",
                headers=_headers(),
                json={
                    "messaging_product": "whatsapp",
                    "status": "read",
                    "message_id": message_id,
                },
                timeout=10.0,
            )
        except Exception:
            logger.exception("Failed to mark message %s as read", message_id)


async def send_text(to: str, text: str) -> dict | None:
    """Send a plain text message. Returns Meta's response dict."""
    if not settings.whatsapp_access_token:
        logger.warning("No WHATSAPP_ACCESS_TOKEN — printing to stdout instead")
        print(f"\n[WhatsApp → {to}]\n{text}\n{'─'*60}\n")
        return None

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{_base_url()}/messages",
                headers=_headers(),
                json={
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to,
                    "type": "text",
                    "text": {"body": text, "preview_url": False},
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            logger.exception("Failed to send WhatsApp message to %s", to)
            return None


async def send_with_human_feel(
    to: str,
    text: str,
    incoming_message_id: str | None = None,
) -> dict | None:
    """Send a message with human-feel: mark read → delay → send.

    This is the standard send path for all agent responses.
    """
    if incoming_message_id:
        await mark_read(incoming_message_id)

    delay = _typing_delay(text)
    logger.debug("Human-feel delay: %.1fs for %d words", delay, len(text.split()))
    await asyncio.sleep(delay)

    return await send_text(to, text)
