"""Profile repository — Supabase queries for user profiles."""

from __future__ import annotations

from app.db.connection import get_service_client


def get_profile_by_id(user_id: str) -> dict | None:
    """Fetch a single profile by user ID."""
    db = get_service_client()
    result = (
        db.table("profiles")
        .select("*")
        .eq("id", user_id)
        .is_("deleted_at", "null")
        .single()
        .execute()
    )
    return result.data


def update_profile(user_id: str, updates: dict) -> dict | None:
    """Update profile fields. Returns updated profile."""
    # Filter out None values — only update provided fields
    filtered = {k: v for k, v in updates.items() if v is not None}
    if not filtered:
        return get_profile_by_id(user_id)

    db = get_service_client()
    result = (
        db.table("profiles")
        .update(filtered)
        .eq("id", user_id)
        .is_("deleted_at", "null")
        .execute()
    )
    return result.data[0] if result.data else None
