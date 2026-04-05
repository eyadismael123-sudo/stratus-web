"""Agent registry — plug-in pattern.

New agent = new class + new row in agent_templates table. Nothing else changes.

AGENT_REGISTRY maps agent slug → agent instance.
route_message() is the main entry point from the WhatsApp webhook.
"""

from __future__ import annotations

import logging

from app.agents.base import BaseAgent
from app.agents.brief.agent import DoctorBriefAgent

logger = logging.getLogger(__name__)

AGENT_REGISTRY: dict[str, BaseAgent] = {
    "brief": DoctorBriefAgent(),
    # "frame": ContentFrameAgent(),   # plug in when built
    # "flash": CarIntelAgent(),        # plug in when built
}


def get_agent(slug: str) -> BaseAgent | None:
    """Return the agent instance for a slug, or None if not registered."""
    return AGENT_REGISTRY.get(slug)


def get_client_agents(client_id: str) -> list[str]:
    """Return the list of agent slugs this client has hired (from DB)."""
    from app.db.connection import get_service_client
    db = get_service_client()
    result = (
        db.table("client_agents")
        .select("agent_slug")
        .eq("client_id", client_id)
        .eq("is_active", True)
        .execute()
    )
    return [row["agent_slug"] for row in (result.data or [])]


def route_message(client_id: str, agent_slug: str | None = None) -> BaseAgent | None:
    """Identify which agent should handle an incoming message.

    If the client has exactly one agent hired, route to that.
    If they have multiple, use Haiku to classify which one the message targets.
    For now: simple first-match logic (expand with Haiku router as agents grow).
    """
    hired = get_client_agents(client_id)
    if not hired:
        logger.info("Client %s has no active agents", client_id)
        return None

    if agent_slug and agent_slug in hired:
        return get_agent(agent_slug)

    # Default: route to the first hired agent
    return get_agent(hired[0])
