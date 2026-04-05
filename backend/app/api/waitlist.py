"""Waitlist endpoint — collect emails for upcoming agents."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import gspread
from fastapi import APIRouter
from google.oauth2.service_account import Credentials
from pydantic import BaseModel, EmailStr

from app.config import settings
from app.db.connection import get_service_client
from app.schemas.common import SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/waitlist", tags=["waitlist"])

_SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _append_to_sheet(email: str, agent: str | None) -> None:
    """Append email + agent + timestamp to Google Sheet. Fails silently — Supabase is the source of truth."""
    if not settings.google_service_account_json or not settings.google_sheet_id:
        logger.warning("Google Sheets not configured — skipping sheet append")
        return

    logger.info("Appending to sheet: email=%s agent=%s", email, agent)
    try:
        creds_dict = json.loads(settings.google_service_account_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=_SHEETS_SCOPES)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(settings.google_sheet_id).sheet1
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        row = [email, agent or "", timestamp]
        logger.info("Sheet row: %s", row)
        sheet.append_row(row)
        logger.info("Sheet append succeeded")
    except Exception:
        # Never let Sheets failure break the signup flow
        logger.exception("Failed to append waitlist email to Google Sheet")


class WaitlistRequest(BaseModel):
    email: EmailStr
    agent: str | None = None  # which agent they signed up for (optional)


@router.post("", response_model=SuccessResponse[dict])
def join_waitlist(body: WaitlistRequest):
    """Add an email to the waitlist. Upserts on email so agent is always updated."""
    logger.info("Waitlist signup: email=%s agent=%s", body.email, body.agent)
    db = get_service_client()

    # Upsert — inserts if new, updates agent if email already exists
    db.table("waitlist").upsert(
        {"email": body.email, "agent": body.agent},
        on_conflict="email",
    ).execute()

    # Mirror to Google Sheets (best-effort — never blocks signup)
    _append_to_sheet(body.email, body.agent)

    return {"success": True, "data": {"status": "registered"}}
