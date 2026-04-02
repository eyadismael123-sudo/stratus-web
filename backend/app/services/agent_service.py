"""Agent service — business logic for agents, logs, and schedules."""

from __future__ import annotations

from datetime import datetime, timezone

from app.exceptions import ConflictError, NotFoundError
from app.repositories import agents as agent_repo
from app.repositories import logs as log_repo
from app.repositories import schedules as schedule_repo


# ─── Marketplace ─────────────────────────────────────────────────────


def list_marketplace_agents(
    category: str | None = None,
    featured: bool | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
) -> tuple[list[dict], int]:
    """List published agent templates for the marketplace."""
    return agent_repo.list_published_templates(
        category=category,
        featured=featured,
        search=search,
        page=page,
        limit=limit,
    )


def get_marketplace_agent(slug: str) -> dict:
    """Fetch a single marketplace agent by slug."""
    template = agent_repo.get_template_by_slug(slug)
    if not template:
        raise NotFoundError("Agent not found")
    return template


# ─── User Agents ─────────────────────────────────────────────────────


def list_user_agents(
    user_id: str,
    status: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[dict], int]:
    """List agents hired by a user."""
    return agent_repo.list_user_agents(
        user_id=user_id, status=status, page=page, limit=limit
    )


def get_user_agent(agent_id: str, user_id: str) -> dict:
    """Fetch a single user agent with ownership check."""
    agent = agent_repo.get_user_agent(agent_id, user_id)
    if not agent:
        raise NotFoundError("Agent not found")
    return agent


def create_user_agent(user_id: str, template_id: str, name: str | None = None) -> dict:
    """Create a user agent record after hiring."""
    template = agent_repo.get_template_by_id(template_id)
    if not template:
        raise NotFoundError("Agent template not found")

    agent_name = name or template["name"]

    data = {
        "user_id": user_id,
        "template_id": template_id,
        "name": agent_name,
        "status": "pending",
        "is_active": False,
        "config": {},
    }
    return agent_repo.create_user_agent(data)


def update_user_agent(agent_id: str, user_id: str, updates: dict) -> dict:
    """Update a user agent after verifying ownership."""
    existing = agent_repo.get_user_agent(agent_id, user_id)
    if not existing:
        raise NotFoundError("Agent not found")

    updated = agent_repo.update_user_agent(agent_id, updates)
    if not updated:
        raise NotFoundError("Agent not found")
    return updated


def delete_user_agent(agent_id: str, user_id: str) -> dict:
    """Soft delete a user agent."""
    deleted = agent_repo.soft_delete_user_agent(agent_id, user_id)
    if not deleted:
        raise NotFoundError("Agent not found")
    return deleted


def activate_agent(agent_id: str) -> dict | None:
    """Activate an agent (called after successful payment)."""
    return agent_repo.update_user_agent(
        agent_id, {"status": "active", "is_active": True}
    )


def deactivate_agent(agent_id: str) -> dict | None:
    """Deactivate an agent (called after subscription cancellation)."""
    return agent_repo.update_user_agent(
        agent_id, {"status": "inactive", "is_active": False}
    )


# ─── Logs ────────────────────────────────────────────────────────────


def list_agent_logs(
    agent_id: str,
    user_id: str,
    status: str | None = None,
    since: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[dict], int]:
    """List logs for a user agent (with ownership check)."""
    agent = agent_repo.get_user_agent(agent_id, user_id)
    if not agent:
        raise NotFoundError("Agent not found")

    return log_repo.list_agent_logs(
        user_agent_id=agent_id, status=status, since=since, page=page, limit=limit
    )


def create_manual_run_log(agent_id: str, user_id: str, input_data: dict | None = None) -> dict:
    """Create a log entry for a manual agent run."""
    agent = agent_repo.get_user_agent(agent_id, user_id)
    if not agent:
        raise NotFoundError("Agent not found")
    if not agent.get("is_active"):
        raise ConflictError("Agent is not active")

    data = {
        "user_agent_id": agent_id,
        "status": "running",
        "trigger_type": "manual",
        "input_data": input_data or {},
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    return log_repo.create_agent_log(data)


# ─── Schedules ───────────────────────────────────────────────────────


def get_schedule(agent_id: str, user_id: str) -> dict:
    """Get schedule for a user agent."""
    agent = agent_repo.get_user_agent(agent_id, user_id)
    if not agent:
        raise NotFoundError("Agent not found")

    schedule = schedule_repo.get_schedule(agent_id)
    if not schedule:
        raise NotFoundError("Schedule not found")
    return schedule


def upsert_schedule(agent_id: str, user_id: str, data: dict) -> dict:
    """Create or update schedule for a user agent."""
    agent = agent_repo.get_user_agent(agent_id, user_id)
    if not agent:
        raise NotFoundError("Agent not found")

    return schedule_repo.upsert_schedule(agent_id, data)


def delete_schedule(agent_id: str, user_id: str) -> dict:
    """Delete schedule for a user agent."""
    agent = agent_repo.get_user_agent(agent_id, user_id)
    if not agent:
        raise NotFoundError("Agent not found")

    deleted = schedule_repo.delete_schedule(agent_id)
    if not deleted:
        raise NotFoundError("Schedule not found")
    return deleted


# ─── Admin ───────────────────────────────────────────────────────────


def list_all_templates(
    published: bool | None = None,
    page: int = 1,
    limit: int = 10,
) -> tuple[list[dict], int]:
    """Admin: list all templates."""
    return agent_repo.list_all_templates(
        published=published, page=page, limit=limit
    )


def create_template(data: dict) -> dict:
    """Admin: create a new agent template."""
    return agent_repo.create_template(data)


def update_template(template_id: str, updates: dict) -> dict:
    """Admin: update an agent template."""
    updated = agent_repo.update_template(template_id, updates)
    if not updated:
        raise NotFoundError("Template not found")
    return updated
