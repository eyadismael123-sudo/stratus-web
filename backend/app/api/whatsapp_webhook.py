"""WhatsApp Cloud API webhook endpoint.

Phase 0 + 1 of the Stratus agent platform.

Handles:
- GET /webhook/whatsapp  — Meta verification handshake
- POST /webhook/whatsapp — Incoming messages + status updates

Processing flow (per framework spec):
  1. Verify HMAC-SHA256 signature
  2. Parse: who sent it, message type
  3. If not a registered client → send "contact Stratus" response
  4. Check onboarding status — if incomplete, continue onboarding
  5. Route to correct agent via AGENT_REGISTRY
  6. Load memory (Layer 2) + master profile (Layer 3)
  7. Build context: memory + profile + last 10 messages
  8. Agent processes → generates response
  9. Human-feel send: mark read → delay → send
  10. Log to agent_logs
"""

from __future__ import annotations

import hashlib
import hmac
import logging

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, Request

from app.agents import memory as mem_store
from app.agents import onboarding as ob_store
from app.agents.human_feel import is_quiet_hours
from app.agents.registry import route_message
from app.config import settings
from app.db.connection import get_service_client
from app.whatsapp.client import send_with_human_feel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["whatsapp"])


# ─── Signature verification ───────────────────────────────────────────────────


def _verify_signature(payload: bytes, signature_header: str) -> bool:
    """Verify Meta HMAC-SHA256 signature. Reject if invalid."""
    if not settings.whatsapp_app_secret:
        logger.warning("WHATSAPP_APP_SECRET not set — skipping signature verification")
        return True  # dev mode: allow through

    expected = "sha256=" + hmac.new(
        settings.whatsapp_app_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header or "")


# ─── Client lookup ────────────────────────────────────────────────────────────


def _get_client(whatsapp_number: str) -> dict | None:
    """Look up a client by WhatsApp number. Returns row or None."""
    db = get_service_client()
    result = (
        db.table("clients")
        .select("*")
        .eq("whatsapp_number", whatsapp_number)
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
    message_id: str,
) -> None:
    """Drive the onboarding state machine for a client+agent."""
    from app.agents.registry import get_agent
    agent = get_agent(agent_slug)
    if not agent:
        return

    session = ob_store.get_session(client["id"], agent_slug)

    if session is None:
        # First message — start onboarding + send intro
        ob_store.start_session(client["id"], agent_slug)
        intro = agent.get_intro_message(client)
        await send_with_human_feel(client["whatsapp_number"], intro, message_id)

        # Ask first question
        first_q = agent.get_onboarding_question(0, {})
        if first_q:
            await send_with_human_feel(client["whatsapp_number"], first_q)
        return

    step = session.get("step", 0)
    collected = session.get("collected_data") or {}

    # Process their answer for the current step
    updated_collected = agent.process_onboarding_answer(step, incoming_text, collected)
    next_step = step + 1

    # Ask next question
    next_q = agent.get_onboarding_question(next_step, updated_collected)

    if next_q is None:
        # Onboarding complete — save memory + mark done
        ob_store.advance_step(client["id"], agent_slug, next_step, updated_collected, complete=True)
        mem_store.save_agent_memory(client["id"], agent_slug, updated_collected)

        peak = updated_collected.get("peak_reading_time", "06:30")
        name = client.get("name", "Doctor")
        completion_msg = (
            f"You're all set, Dr. {name.split()[-1]}.\n\n"
            f"Your first briefing arrives at {peak} tomorrow morning. "
            f"I'll cover {', '.join(updated_collected.get('clinical_focus', [])[:2])} "
            f"from {', '.join(updated_collected.get('trusted_journals', [])[:2])} and beyond.\n\n"
            f"Any questions before then? Just message me."
        )
        await send_with_human_feel(client["whatsapp_number"], completion_msg, message_id)
    else:
        ob_store.advance_step(client["id"], agent_slug, next_step, updated_collected)
        await send_with_human_feel(client["whatsapp_number"], next_q, message_id)


# ─── Webhook endpoints ────────────────────────────────────────────────────────


@router.get("/whatsapp")
def whatsapp_verify(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
):
    """Meta webhook verification handshake (GET)."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("WhatsApp webhook verified by Meta")
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(default="", alias="x-hub-signature-256"),
):
    """Receive incoming WhatsApp messages (POST)."""
    payload = await request.body()

    if not _verify_signature(payload, x_hub_signature_256):
        logger.warning("Invalid WhatsApp webhook signature — rejecting")
        raise HTTPException(status_code=401, detail="Invalid signature")

    body = await request.json()

    # WhatsApp wraps everything in entry[].changes[]
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])

            for msg in messages:
                background_tasks.add_task(_process_message, msg, value)

    # Meta requires a 200 immediately
    return {"status": "ok"}


async def _process_message(msg: dict, value: dict) -> None:
    """Process a single incoming WhatsApp message."""
    message_id = msg.get("id", "")
    from_number = msg.get("from", "")
    msg_type = msg.get("type", "text")

    # Extract text (expand for voice/image in Phase 3)
    if msg_type == "text":
        text = msg.get("text", {}).get("body", "").strip()
    else:
        # Phase 3: voice → Whisper, image → Vision
        logger.info("Unsupported message type=%s — skipping for now", msg_type)
        return

    if not text or not from_number:
        return

    logger.info("Incoming WhatsApp from=%s type=%s", from_number, msg_type)

    # Look up client
    client = _get_client(from_number)
    if not client:
        logger.info("Unknown number %s — sending contact response", from_number)
        await send_with_human_feel(
            from_number,
            "Hi! I'm Brief from Stratus. To get started, visit stratus.ai or contact us to set up your agent.",
            message_id,
        )
        return

    client_id = client["id"]
    timezone_str = client.get("timezone", "Asia/Dubai")

    # Quiet hours: don't respond between 23:00–06:00
    if is_quiet_hours(timezone_str):
        logger.info("Quiet hours for client=%s — not responding", client_id)
        return

    # Determine which agent the client has hired
    from app.agents.registry import get_client_agents
    hired_slugs = get_client_agents(client_id)

    if not hired_slugs:
        await send_with_human_feel(
            from_number,
            "You don't have any active agents yet. Visit stratus.ai to get started.",
            message_id,
        )
        return

    agent_slug = hired_slugs[0]  # expand with Haiku router as agents multiply

    # Log the incoming message
    mem_store.log_message(
        client_id=client_id,
        agent_slug=agent_slug,
        direction="in",
        message_type=msg_type,
        raw_content=text,
    )

    # Onboarding check
    if not ob_store.is_complete(client_id, agent_slug):
        await _handle_onboarding(client, agent_slug, text, message_id)
        return

    # Normal message handling — load memory + profile + recent context
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

    await send_with_human_feel(from_number, reply, message_id)
