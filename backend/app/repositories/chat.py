"""Chat repository — conversations + messages DB queries."""

from __future__ import annotations

from app.db.connection import get_service_client


# ─── Conversations ────────────────────────────────────────────────────


def create_conversation(client_id: str, agent_id: str | None = None) -> dict:
    db = get_service_client()
    result = (
        db.table("conversations")
        .insert({"client_id": client_id, "agent_id": agent_id})
        .execute()
    )
    if not result.data:
        raise ValueError("Failed to create conversation")
    return result.data[0]


def get_conversation(conversation_id: str, client_id: str) -> dict | None:
    db = get_service_client()
    result = (
        db.table("conversations")
        .select("*")
        .eq("id", conversation_id)
        .eq("client_id", client_id)
        .single()
        .execute()
    )
    return result.data


def list_conversations(client_id: str) -> list[dict]:
    db = get_service_client()
    result = (
        db.table("conversations")
        .select("*")
        .eq("client_id", client_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


# ─── Messages ─────────────────────────────────────────────────────────


def insert_message(
    conversation_id: str,
    role: str,
    content: str,
    tokens_used: int | None = None,
) -> dict:
    db = get_service_client()
    result = (
        db.table("messages")
        .insert(
            {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "tokens_used": tokens_used,
            }
        )
        .execute()
    )
    if not result.data:
        raise ValueError("Failed to insert message")
    return result.data[0]


def list_messages(conversation_id: str, limit: int = 50) -> list[dict]:
    db = get_service_client()
    result = (
        db.table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    return result.data or []


def get_recent_messages(conversation_id: str, limit: int = 10) -> list[dict]:
    """Fetch the N most recent messages for context injection."""
    db = get_service_client()
    result = (
        db.table("messages")
        .select("role, content, created_at")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    # Return in chronological order
    return list(reversed(result.data or []))
