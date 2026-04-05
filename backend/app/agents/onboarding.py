"""Generic onboarding state machine.

Tracks onboarding progress via the onboarding_sessions table.
Each agent defines its own questions/steps via BaseAgent methods.
"""

from __future__ import annotations

import logging

from app.db.connection import get_service_client

logger = logging.getLogger(__name__)


def get_session(client_id: str, agent_slug: str) -> dict | None:
    """Return the onboarding session row, or None if not started."""
    db = get_service_client()
    result = (
        db.table("onboarding_sessions")
        .select("*")
        .eq("client_id", client_id)
        .eq("agent_slug", agent_slug)
        .maybe_single()
        .execute()
    )
    return result.data


def is_complete(client_id: str, agent_slug: str) -> bool:
    """Return True if onboarding is finished for this client+agent."""
    session = get_session(client_id, agent_slug)
    return bool(session and session.get("is_complete"))


def start_session(client_id: str, agent_slug: str) -> dict:
    """Create a new onboarding session at step 0."""
    db = get_service_client()
    db.table("onboarding_sessions").insert({
        "client_id": client_id,
        "agent_slug": agent_slug,
        "step": 0,
        "collected_data": {},
        "is_complete": False,
    }).execute()
    return {"step": 0, "collected_data": {}, "is_complete": False}


def advance_step(
    client_id: str,
    agent_slug: str,
    new_step: int,
    collected_data: dict,
    complete: bool = False,
) -> None:
    """Update step and collected_data for an ongoing session."""
    db = get_service_client()
    db.table("onboarding_sessions").update({
        "step": new_step,
        "collected_data": collected_data,
        "is_complete": complete,
    }).eq("client_id", client_id).eq("agent_slug", agent_slug).execute()
