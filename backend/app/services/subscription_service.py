"""Subscription service — business logic for billing records."""

from __future__ import annotations

import logging

from app.exceptions import ConflictError, NotFoundError
from app.repositories import subscriptions as sub_repo
from app.services import agent_service, stripe_service

logger = logging.getLogger(__name__)


def list_subscriptions(user_id: str) -> list[dict]:
    """List all subscriptions for a user."""
    return sub_repo.list_user_subscriptions(user_id)


def cancel_subscription(subscription_id: str, user_id: str, reason: str | None = None) -> dict:
    """Cancel a subscription at period end."""
    sub = sub_repo.get_subscription_by_id(subscription_id, user_id)
    if not sub:
        raise NotFoundError("Subscription not found")
    if sub["status"] == "canceled":
        raise ConflictError("Subscription is already canceled")

    stripe_service.cancel_subscription(sub["stripe_subscription_id"])

    updates = {"cancel_at_period_end": True}
    if reason:
        updates["cancellation_reason"] = reason

    updated = sub_repo.update_subscription(subscription_id, updates)
    if not updated:
        raise NotFoundError("Subscription not found")
    return updated


def reactivate_subscription(subscription_id: str, user_id: str) -> dict:
    """Reactivate a subscription that was set to cancel at period end."""
    sub = sub_repo.get_subscription_by_id(subscription_id, user_id)
    if not sub:
        raise NotFoundError("Subscription not found")
    if not sub.get("cancel_at_period_end"):
        raise ConflictError("Subscription is not scheduled for cancellation")

    stripe_service.reactivate_subscription(sub["stripe_subscription_id"])

    updated = sub_repo.update_subscription(
        subscription_id, {"cancel_at_period_end": False}
    )
    if not updated:
        raise NotFoundError("Subscription not found")
    return updated


# ─── Webhook Handlers ────────────────────────────────────────────────


def handle_subscription_created(data: dict) -> None:
    """Handle customer.subscription.created webhook event."""
    try:
        stripe_sub = data["object"]
        metadata = stripe_sub.get("metadata", {})

        user_id = metadata.get("user_id")
        user_agent_id = metadata.get("user_agent_id")

        if not user_id or not user_agent_id:
            logger.warning(f"Webhook missing metadata: {stripe_sub['id']}")
            return

        sub_data = {
            "user_id": user_id,
            "user_agent_id": user_agent_id,
            "stripe_subscription_id": stripe_sub["id"],
            "stripe_customer_id": stripe_sub["customer"],
            "status": stripe_sub["status"],
            "current_period_start": stripe_sub["current_period_start"],
            "current_period_end": stripe_sub["current_period_end"],
            "cancel_at_period_end": stripe_sub.get("cancel_at_period_end", False),
        }
        sub_repo.create_subscription(sub_data)
        logger.info(f"Created subscription {stripe_sub['id']} for user {user_id}")

        if stripe_sub["status"] == "active":
            agent_service.activate_agent(user_agent_id)
            logger.info(f"Activated agent {user_agent_id}")
    except Exception:
        logger.exception("Failed to handle subscription.created")
        raise


def handle_subscription_updated(data: dict) -> None:
    """Handle customer.subscription.updated webhook event."""
    try:
        stripe_sub = data["object"]
        stripe_sub_id = stripe_sub["id"]

        updates = {
            "status": stripe_sub["status"],
            "current_period_start": stripe_sub["current_period_start"],
            "current_period_end": stripe_sub["current_period_end"],
            "cancel_at_period_end": stripe_sub.get("cancel_at_period_end", False),
        }

        if stripe_sub.get("canceled_at"):
            updates["canceled_at"] = stripe_sub["canceled_at"]

        sub_repo.update_subscription_by_stripe_id(stripe_sub_id, updates)

        existing = sub_repo.get_subscription_by_stripe_id(stripe_sub_id)
        if existing:
            agent_id = existing["user_agent_id"]
            if stripe_sub["status"] == "active":
                agent_service.activate_agent(agent_id)
            elif stripe_sub["status"] in ("past_due", "unpaid", "canceled"):
                agent_service.deactivate_agent(agent_id)
        logger.info(f"Updated subscription {stripe_sub_id} → {stripe_sub['status']}")
    except Exception:
        logger.exception("Failed to handle subscription.updated")
        raise


def handle_subscription_deleted(data: dict) -> None:
    """Handle customer.subscription.deleted webhook event."""
    try:
        stripe_sub = data["object"]
        stripe_sub_id = stripe_sub["id"]

        sub_repo.update_subscription_by_stripe_id(
            stripe_sub_id, {"status": "canceled"}
        )

        existing = sub_repo.get_subscription_by_stripe_id(stripe_sub_id)
        if existing:
            agent_service.deactivate_agent(existing["user_agent_id"])
        logger.info(f"Deleted subscription {stripe_sub_id}")
    except Exception:
        logger.exception("Failed to handle subscription.deleted")
        raise


def handle_invoice_payment_failed(data: dict) -> None:
    """Handle invoice.payment_failed webhook event."""
    try:
        invoice = data["object"]
        stripe_sub_id = invoice.get("subscription")
        if not stripe_sub_id:
            return

        sub_repo.update_subscription_by_stripe_id(
            stripe_sub_id, {"status": "past_due"}
        )

        existing = sub_repo.get_subscription_by_stripe_id(stripe_sub_id)
        if existing:
            agent_service.deactivate_agent(existing["user_agent_id"])
        logger.warning(f"Payment failed for subscription {stripe_sub_id}")
    except Exception:
        logger.exception("Failed to handle invoice.payment_failed")
        raise
