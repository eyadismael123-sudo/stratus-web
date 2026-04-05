"""Agent memory layer — read/write for agent_memory and user_profiles tables.

Layer 2 — Agent Memory (per-agent per-client JSONB, Haiku updates after each interaction)
Layer 3 — Master Profile (Sonnet weekly synthesis, cross-agent understanding)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.db.connection import get_service_client

logger = logging.getLogger(__name__)


def load_agent_memory(client_id: str, agent_slug: str) -> dict:
    """Load agent-specific memory for a client. Returns empty dict if not found."""
    db = get_service_client()
    result = (
        db.table("agent_memory")
        .select("memory_json")
        .eq("client_id", client_id)
        .eq("agent_slug", agent_slug)
        .maybe_single()
        .execute()
    )
    if result.data:
        return result.data.get("memory_json") or {}
    return {}


def save_agent_memory(client_id: str, agent_slug: str, memory: dict) -> None:
    """Upsert agent memory (creates if missing, updates if exists)."""
    db = get_service_client()
    db.table("agent_memory").upsert(
        {
            "client_id": client_id,
            "agent_slug": agent_slug,
            "memory_json": memory,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="client_id,agent_slug",
    ).execute()


def load_master_profile(client_id: str) -> dict:
    """Load the client's master personality profile. Returns empty dict if not found."""
    db = get_service_client()
    result = (
        db.table("user_profiles")
        .select("profile_json")
        .eq("client_id", client_id)
        .maybe_single()
        .execute()
    )
    if result.data:
        return result.data.get("profile_json") or {}
    return {}


def save_master_profile(client_id: str, profile: dict) -> None:
    """Upsert master profile."""
    db = get_service_client()
    db.table("user_profiles").upsert(
        {
            "client_id": client_id,
            "profile_json": profile,
            "last_summarized_at": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="client_id",
    ).execute()


def log_message(
    client_id: str,
    agent_slug: str,
    direction: str,  # "in" | "out"
    message_type: str,  # "text" | "voice" | "image" | "video"
    raw_content: str,
    processed_content: str = "",
    response: str = "",
    tokens_used: int = 0,
) -> None:
    """Append a message to agent_logs (Layer 1 — raw audit trail)."""
    db = get_service_client()
    try:
        db.table("agent_logs").insert({
            "client_id": client_id,
            "agent_slug": agent_slug,
            "direction": direction,
            "message_type": message_type,
            "raw_content": raw_content,
            "processed_content": processed_content,
            "response": response,
            "tokens_used": tokens_used,
        }).execute()
    except Exception:
        logger.exception("Failed to log message for client=%s agent=%s", client_id, agent_slug)


def get_recent_messages(client_id: str, agent_slug: str, limit: int = 10) -> list[dict]:
    """Fetch last N messages from agent_logs for context building."""
    db = get_service_client()
    result = (
        db.table("agent_logs")
        .select("direction, message_type, raw_content, response, created_at")
        .eq("client_id", client_id)
        .eq("agent_slug", agent_slug)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(result.data or []))
