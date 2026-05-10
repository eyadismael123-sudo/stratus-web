"""LinkedIn Ghostwriter API endpoints.

Handles OAuth connect/callback and read-only session/post history endpoints.
The interactive post flow runs via Telegram — these endpoints serve the dashboard.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.agents.linkedin.linkedin_api import get_profile
from app.agents.linkedin.oauth import exchange_code, generate_auth_url
from app.config import settings
from app.db.connection import get_service_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/linkedin", tags=["linkedin"])


# ─── OAuth ────────────────────────────────────────────────────────────────────


@router.get("/oauth/connect")
def linkedin_oauth_connect(client_id: str = Query(..., description="Stratus client UUID")):
    """Generate a LinkedIn OAuth authorization URL for the given client."""
    if not settings.linkedin_client_id:
        raise HTTPException(503, "LinkedIn OAuth is not configured on this server")
    auth_url, _ = generate_auth_url(client_id)
    return {"auth_url": auth_url}


@router.get("/oauth/callback")
def linkedin_oauth_callback(code: str = Query(...), state: str = Query(...)):
    """Handle LinkedIn OAuth callback.

    Exchanges the code for tokens, fetches the LinkedIn profile, and
    upserts the linkedin_accounts row for this client.
    """
    try:
        client_id, _ = state.split(":", 1)
    except ValueError:
        raise HTTPException(400, "Invalid state parameter")

    try:
        tokens = exchange_code(code)
    except Exception:
        logger.exception("LinkedIn code exchange failed")
        raise HTTPException(502, "LinkedIn token exchange failed — please try again")

    try:
        profile = get_profile(tokens["access_token"])
    except Exception:
        logger.exception("LinkedIn profile fetch failed")
        raise HTTPException(502, "Could not fetch LinkedIn profile")

    linkedin_user_id = profile.get("sub", "")
    if not linkedin_user_id:
        raise HTTPException(502, "LinkedIn profile missing user ID")

    db = get_service_client()
    db.table("linkedin_accounts").upsert(
        {
            "client_id": client_id,
            "linkedin_user_id": linkedin_user_id,
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token"),
            "token_expires_at": tokens.get("expires_at"),
            "linkedin_name": profile.get("name", ""),
            "linkedin_email": profile.get("email", ""),
            "is_active": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="client_id",
    ).execute()

    linkedin_name = profile.get("name", "")
    return {"ok": True, "linkedin_name": linkedin_name, "message": "LinkedIn connected successfully"}


# ─── Voice profile ────────────────────────────────────────────────────────────


@router.get("/voice/{client_id}")
def get_voice_profile(client_id: str):
    """Fetch the extracted voice profile for a client (dashboard display)."""
    db = get_service_client()
    result = (
        db.table("voice_profiles")
        .select("*")
        .eq("client_id", client_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(404, "No voice profile found for this client")
    return result.data


# ─── Session history ──────────────────────────────────────────────────────────


@router.get("/sessions/{client_id}")
def list_sessions(client_id: str, limit: int = Query(20, ge=1, le=100)):
    """List recent LinkedIn post sessions for a client (dashboard)."""
    db = get_service_client()
    result = (
        db.table("linkedin_post_sessions")
        .select("id, topic, state, selected_version, linkedin_post_id, posted_at, created_at")
        .eq("client_id", client_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"sessions": result.data or []}


@router.get("/posts/{client_id}")
def list_posts(client_id: str, limit: int = Query(20, ge=1, le=100)):
    """List published LinkedIn posts for a client."""
    db = get_service_client()
    result = (
        db.table("linkedin_posts")
        .select("id, topic, content, linkedin_post_id, posted_at")
        .eq("client_id", client_id)
        .order("posted_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"posts": result.data or []}
