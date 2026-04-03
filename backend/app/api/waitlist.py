"""Waitlist endpoint — collect emails for upcoming agents."""

from __future__ import annotations

from fastapi import APIRouter

from app.db.connection import get_service_client
from app.exceptions import ConflictError
from app.schemas.common import SuccessResponse
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/waitlist", tags=["waitlist"])


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
        # Already signed up — return success silently (no need to tell them it's a dupe)
        return {"success": True, "data": {"status": "already_registered"}}

    db.table("waitlist").insert({"email": body.email}).execute()
    return {"success": True, "data": {"status": "registered"}}
