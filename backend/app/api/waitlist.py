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


def _append_to_sheet(email: str) -> None:
    """Append email + timestamp to Google Sheet. Fails silently — Supabase is the source of truth."""
    if not settings.google_service_account_json or not settings.google_sheet_id:
        return  # Sheets not configured yet — skip silently

    try:
        creds_dict = json.loads(settings.google_service_account_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=_SHEETS_SCOPES)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(settings.google_sheet_id).sheet1
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        sheet.append_row([email, timestamp])
    except Exception:
        # Never let Sheets failure break the signup flow
        logger.exception("Failed to append waitlist email to Google Sheet")


class WaitlistRequest(BaseModel):
    email: EmailStr


@router.post("", response_model=SuccessResponse[dict])
def join_waitlist(body: WaitlistRequest):
    """Add an email to the waitlist. Idempotent — duplicate emails return success."""
    db = get_service_client()

    # Check if already on the list
    existing = (
        db.table("waitlist")
        .select("id")
        .eq("email", body.email)
        .execute()
    )
    if existing.data:
        return {"success": True, "data": {"status": "already_registered"}}

    db.table("waitlist").insert({"email": body.email}).execute()

    # Mirror to Google Sheets (best-effort — never blocks signup)
    _append_to_sheet(body.email)

    return {"success": True, "data": {"status": "registered"}}
