"""Agent repository — Supabase queries for templates + user agents."""

from __future__ import annotations

from typing import Any

from app.db.connection import get_service_client


# ─── Agent Templates ──────────────────────────────────────────────────


def list_published_templates(
    category: str | None = None,
    featured: bool | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
) -> tuple[list[dict], int]:
    """List published agent templates with filtering + pagination."""
    db = get_service_client()
    query = (
        db.table("agent_templates")
        .select("*", count="exact")
        .eq("is_published", True)
        .is_("deleted_at", "null")
    )

    if category:
        query = query.eq("category", category)
    if featured is not None:
        query = query.eq("is_featured", featured)
    if search:
        query = query.or_(
            f"name.ilike.%{search}%,description.ilike.%{search}%"
        )

    offset = (page - 1) * limit
    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()
    total = result.count if result.count is not None else 0
    return result.data or [], total


def get_template_by_slug(slug: str) -> dict | None:
    """Fetch a single template by slug."""
    db = get_service_client()
    result = (
        db.table("agent_templates")
        .select("*")
        .eq("slug", slug)
        .eq("is_published", True)
        .is_("deleted_at", "null")
        .single()
        .execute()
    )
    return result.data


def get_template_by_id(template_id: str) -> dict | None:
    """Fetch a single template by ID (any status)."""
    db = get_service_client()
    result = (
        db.table("agent_templates")
        .select("*")
        .eq("id", template_id)
        .is_("deleted_at", "null")
        .single()
        .execute()
    )
    return result.data


# ─── Admin Templates ──────────────────────────────────────────────────


def list_all_templates(
    published: bool | None = None,
    page: int = 1,
    limit: int = 10,
) -> tuple[list[dict], int]:
    """Admin: list all templates (published + unpublished)."""
    db = get_service_client()
    query = (
        db.table("agent_templates")
        .select("*", count="exact")
        .is_("deleted_at", "null")
    )

    if published is not None:
        query = query.eq("is_published", published)

    offset = (page - 1) * limit
    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()
    total = result.count if result.count is not None else 0
    return result.data or [], total


def create_template(data: dict) -> dict:
    """Admin: create a new agent template."""
    db = get_service_client()
    result = db.table("agent_templates").insert(data).execute()
    if not result.data:
        raise ValueError("Failed to create template")
    return result.data[0]


def update_template(template_id: str, updates: dict) -> dict | None:
    """Admin: update an agent template."""
    filtered = {k: v for k, v in updates.items() if v is not None}
    if not filtered:
        return get_template_by_id(template_id)

    db = get_service_client()
    result = (
        db.table("agent_templates")
        .update(filtered)
        .eq("id", template_id)
        .execute()
    )
    return result.data[0] if result.data else None


# ─── User Agents ──────────────────────────────────────────────────────


def list_user_agents(
    user_id: str,
    status: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[dict], int]:
    """List agents hired by a specific user."""
    db = get_service_client()
    query = (
        db.table("user_agents")
        .select("*, agent_templates(id, name, slug, icon_url, category, role)", count="exact")
        .eq("user_id", user_id)
        .is_("deleted_at", "null")
    )

    if status:
        query = query.eq("status", status)

    offset = (page - 1) * limit
    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()
    total = result.count if result.count is not None else 0
    return result.data or [], total


def get_user_agent(agent_id: str, user_id: str) -> dict | None:
    """Fetch a single user agent (ownership enforced)."""
    db = get_service_client()
    result = (
        db.table("user_agents")
        .select("*, agent_templates(id, name, slug, icon_url, category, role)")
        .eq("id", agent_id)
        .eq("user_id", user_id)
        .is_("deleted_at", "null")
        .single()
        .execute()
    )
    return result.data


def create_user_agent(data: dict) -> dict:
    """Create a new user agent record."""
    db = get_service_client()
    result = db.table("user_agents").insert(data).execute()
    if not result.data:
        raise ValueError("Failed to create user agent")
    return result.data[0]


def update_user_agent(agent_id: str, updates: dict) -> dict | None:
    """Update a user agent record."""
    filtered = {k: v for k, v in updates.items() if v is not None}
    if not filtered:
        return None

    db = get_service_client()
    result = (
        db.table("user_agents")
        .update(filtered)
        .eq("id", agent_id)
        .execute()
    )
    return result.data[0] if result.data else None


def soft_delete_user_agent(agent_id: str, user_id: str) -> dict | None:
    """Soft delete a user agent."""
    from datetime import datetime, timezone

    db = get_service_client()
    result = (
        db.table("user_agents")
        .update({"deleted_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", agent_id)
        .eq("user_id", user_id)
        .execute()
    )
    return result.data[0] if result.data else None


def get_user_agent_by_id(agent_id: str) -> dict | None:
    """Fetch a user agent by ID without ownership check (for webhooks)."""
    db = get_service_client()
    result = (
        db.table("user_agents")
        .select("*")
        .eq("id", agent_id)
        .single()
        .execute()
    )
    return result.data
