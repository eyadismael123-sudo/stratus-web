"""Client subscription service — Stripe billing for Telegram-native clients.

Manages activation/deactivation of client_agents rows based on Stripe events.
Used by the LinkedIn Agent MVP (and any future Telegram-first agents).
"""

from __future__ import annotations

import logging

from app.db.connection import get_service_client

logger = logging.getLogger(__name__)


def activate_client_agent(
    stripe_subscription_id: str,
    stripe_customer_id: str,
    client_id: str,
    agent_slug: str,
    stripe_status: str,
) -> None:
    """Activate a client_agents row after successful Stripe payment.

    - Creates the client_agents row if it doesn't exist yet.
    - Saves the Stripe subscription ID and customer ID.
    - Sets is_active = TRUE so the bot starts accepting messages.
    """
    db = get_service_client()

    # Persist Stripe customer ID on the client record
    if stripe_customer_id:
        db.table("clients").update(
            {"stripe_customer_id": stripe_customer_id}
        ).eq("id", client_id).execute()

    # Upsert client_agents: activate if exists, create if not
    db.table("client_agents").upsert(
        {
            "client_id": client_id,
            "agent_slug": agent_slug,
            "is_active": True,
            "stripe_subscription_id": stripe_subscription_id,
            "stripe_subscription_status": stripe_status,
        },
        on_conflict="client_id,agent_slug",
    ).execute()

    logger.info(
        "Activated agent=%s for client=%s (stripe_sub=%s)",
        agent_slug,
        client_id,
        stripe_subscription_id,
    )


def deactivate_client_agent(
    stripe_subscription_id: str,
    stripe_status: str,
) -> bool:
    """Deactivate a client_agents row by Stripe subscription ID.

    Returns True if a matching row was found and updated.
    """
    db = get_service_client()

    result = (
        db.table("client_agents")
        .update({"is_active": False, "stripe_subscription_status": stripe_status})
        .eq("stripe_subscription_id", stripe_subscription_id)
        .execute()
    )

    updated = bool(result.data)
    if updated:
        logger.info(
            "Deactivated client_agents for stripe_sub=%s (status=%s)",
            stripe_subscription_id,
            stripe_status,
        )
    return updated


def deactivate_client_agent_by_stripe_id(
    stripe_subscription_id: str,
    stripe_status: str,
) -> bool:
    """Attempt to deactivate by Stripe subscription ID. Returns True if found."""
    return deactivate_client_agent(stripe_subscription_id, stripe_status)
