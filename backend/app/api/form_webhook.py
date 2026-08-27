"""Google Form onboarding intake — Brief agent.

Doctors fill in a Google Form. An Apps Script "on form submit" trigger
POSTs the responses here. This creates (or updates) their client row,
activates their Brief subscription, writes their full agent memory, and
marks onboarding complete — so the moment they message the Brief bot for
the first time (matched by the @username they gave in the form), Telegram
identity sync fills in their chat_id and their very first message can be a
real briefing, no conversational onboarding needed.

Auth: shared secret in the X-Form-Secret header, set by the Apps Script
and compared against settings.form_webhook_secret. Reject everything if
the secret isn't configured — an unauthenticated intake endpoint that
writes active $50/mo subscriptions is not something to leave open by
accident.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Request

from app.agents import memory as mem_store
from app.agents import onboarding as ob_store
from app.config import settings
from app.db.connection import get_service_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["form"])

_DEFAULT_FORMAT = "3 papers, 2-sentence summary each, link at end"
_DEFAULT_PEAK_TIME = "06:30"
_DEFAULT_TIMEZONE = "Asia/Dubai"


def _verify_secret(secret_header: str | None) -> None:
    if not settings.form_webhook_secret:
        logger.error("FORM_WEBHOOK_SECRET not set — rejecting all form submissions")
        raise HTTPException(status_code=503, detail="Form intake not configured")
    if not secret_header or secret_header != settings.form_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid or missing form secret")


def _split_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.replace("\n", ",").split(",") if item.strip()]


def _normalize_telegram_username(raw: str) -> str:
    return raw.strip().lstrip("@")


def _get_or_create_client(name: str, telegram_username: str, timezone_str: str) -> str:
    db = get_service_client()

    existing = (
        db.table("clients")
        .select("id")
        .eq("telegram_username", telegram_username)
        .maybe_single()
        .execute()
    )
    if existing.data:
        client_id = existing.data["id"]
        db.table("clients").update({
            "name": name,
            "timezone": timezone_str,
            "is_active": True,
        }).eq("id", client_id).execute()
        logger.info("Form intake: updated existing client=%s (@%s)", client_id, telegram_username)
        return client_id

    created = db.table("clients").insert({
        "name": name,
        "telegram_username": telegram_username,
        "timezone": timezone_str,
        "is_active": True,
    }).execute()
    client_id = created.data[0]["id"]
    logger.info("Form intake: created client=%s (@%s)", client_id, telegram_username)
    return client_id


def _activate_brief_subscription(client_id: str) -> None:
    db = get_service_client()
    existing = (
        db.table("client_agents")
        .select("id")
        .eq("client_id", client_id)
        .eq("agent_slug", "brief")
        .maybe_single()
        .execute()
    )
    if existing.data:
        db.table("client_agents").update({"is_active": True}).eq("id", existing.data["id"]).execute()
    else:
        db.table("client_agents").insert({
            "client_id": client_id,
            "agent_slug": "brief",
            "is_active": True,
        }).execute()


@router.post("/form/brief")
async def brief_form_submission(
    request: Request,
    x_form_secret: str | None = Header(default=None),
) -> dict:
    """Receive a Brief onboarding submission from the Google Form."""
    _verify_secret(x_form_secret)
    body = await request.json()

    name = (body.get("name") or "").strip()
    telegram_username = _normalize_telegram_username(body.get("telegram_username") or "")
    specialty = (body.get("specialty") or "").strip()

    if not name or not telegram_username or not specialty:
        raise HTTPException(
            status_code=422,
            detail="name, telegram_username, and specialty are required",
        )

    institution = (body.get("institution") or "").strip()
    timezone_str = (body.get("timezone") or _DEFAULT_TIMEZONE).strip()
    clinical_focus = _split_list(body.get("clinical_focus") or "")
    trusted_journals = _split_list(body.get("trusted_journals") or "")
    dislikes = _split_list(body.get("dislikes") or "")
    peak_reading_time = (body.get("peak_reading_time") or "").strip() or _DEFAULT_PEAK_TIME
    preferred_format = (body.get("preferred_format") or "").strip() or _DEFAULT_FORMAT

    client_id = _get_or_create_client(name, telegram_username, timezone_str)
    _activate_brief_subscription(client_id)

    collected = {
        "specialty": specialty,
        "institution": institution,
        "clinical_focus": clinical_focus,
        "trusted_journals": trusted_journals,
        "dislikes": dislikes,
        "peak_reading_time": peak_reading_time,
        "preferred_format": preferred_format,
        "familiarity_level": 0,
    }
    mem_store.save_agent_memory(client_id, "brief", collected)

    if ob_store.get_session(client_id, "brief") is None:
        ob_store.start_session(client_id, "brief")
    ob_store.advance_step(client_id, "brief", 6, collected, complete=True)

    logger.info(
        "Form intake: onboarded client=%s specialty=%r peak_time=%s",
        client_id, specialty, peak_reading_time,
    )
    return {"ok": True, "client_id": client_id}
