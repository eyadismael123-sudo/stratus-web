"""Agent logs repository — Supabase queries for run history."""

from __future__ import annotations

from typing import Any

from app.db.connection import get_service_client


def list_agent_logs(
    user_agent_id: str,
    status: str | None = None,
    since: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[dict], int]:
    """List paginated logs for a specific user agent."""
    db = get_service_client()
    query = (
        db.table("agent_logs")
        .select("*", count="exact")
        .eq("user_agent_id", user_agent_id)
    )

    if status:
        query = query.eq("status", status)
    if since:
        query = query.gte("created_at", since)

    offset = (page - 1) * limit
    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()
    total = result.count if result.count is not None else 0
    return result.data or [], total


def create_agent_log(data: dict) -> dict:
    """Create a new agent log entry."""
    db = get_service_client()
    result = db.table("agent_logs").insert(data).execute()
    if not result.data:
        raise ValueError("Failed to create agent log")
    return result.data[0]


def list_logs_for_user_today(user_id: str, today_start: str) -> list[dict]:
    """Fetch all logs for a user's agents from today (for outcome receipts)."""
    db = get_service_client()

    # First get all user agent IDs
    agents_result = (
        db.table("user_agents")
        .select("id")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .execute()
    )
    if not agents_result.data:
        return []

    agent_ids = [a["id"] for a in agents_result.data]

    result = (
        db.table("agent_logs")
        .select("*, user_agents(name, agent_templates(name))")
        .in_("user_agent_id", agent_ids)
        .gte("created_at", today_start)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []
