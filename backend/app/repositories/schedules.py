"""Agent schedule repository — Supabase queries for cron schedules."""

from __future__ import annotations

from app.db.connection import get_service_client


def get_schedule(user_agent_id: str) -> dict | None:
    """Fetch the schedule for a user agent."""
    db = get_service_client()
    result = (
        db.table("agent_schedules")
        .select("*")
        .eq("user_agent_id", user_agent_id)
        .single()
        .execute()
    )
    return result.data


def upsert_schedule(user_agent_id: str, data: dict) -> dict:
    """Create or update a schedule for a user agent."""
    db = get_service_client()

    existing = get_schedule(user_agent_id)
    if existing:
        result = (
            db.table("agent_schedules")
            .update(data)
            .eq("user_agent_id", user_agent_id)
            .execute()
        )
    else:
        result = (
            db.table("agent_schedules")
            .insert({**data, "user_agent_id": user_agent_id})
            .execute()
        )
    if not result.data:
        raise ValueError("Failed to upsert schedule")
    return result.data[0]


def delete_schedule(user_agent_id: str) -> dict | None:
    """Delete the schedule for a user agent."""
    db = get_service_client()
    result = (
        db.table("agent_schedules")
        .delete()
        .eq("user_agent_id", user_agent_id)
        .execute()
    )
    return result.data[0] if result.data else None
