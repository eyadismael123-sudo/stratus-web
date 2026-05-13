"""Webhook endpoints — Stripe event processing.

Two routing paths based on metadata keys in the Stripe event:
- metadata.client_id  → LinkedIn agent MVP (clients + client_agents tables)
- metadata.user_id    → Web platform (profiles + user_agents tables)
"""

import logging

from fastapi import APIRouter, Header, Request

from app.services import client_subscription_service, stripe_service, subscription_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _route_subscription_event(data: dict, active: bool) -> None:
    """Route a subscription lifecycle event to the correct service based on metadata."""
    stripe_sub = data["object"]
    metadata = stripe_sub.get("metadata", {})

    if metadata.get("client_id"):
        # LinkedIn agent MVP path
        if active:
            client_subscription_service.activate_client_agent(
                stripe_sub["id"],
                stripe_sub.get("customer", ""),
                metadata["client_id"],
                metadata.get("agent_slug", "linkedin"),
                stripe_sub["status"],
            )
        else:
            client_subscription_service.deactivate_client_agent(
                stripe_sub["id"],
                stripe_sub["status"],
            )
    elif metadata.get("user_id"):
        # Web platform path — delegate to existing handler
        if active:
            subscription_service.handle_subscription_created(data)
        else:
            subscription_service.handle_subscription_updated(data)


def _handle_subscription_created(data: dict) -> None:
    stripe_sub = data["object"]
    metadata = stripe_sub.get("metadata", {})
    if metadata.get("client_id"):
        client_subscription_service.activate_client_agent(
            stripe_sub["id"],
            stripe_sub.get("customer", ""),
            metadata["client_id"],
            metadata.get("agent_slug", "linkedin"),
            stripe_sub["status"],
        )
    else:
        subscription_service.handle_subscription_created(data)


def _handle_subscription_updated(data: dict) -> None:
    stripe_sub = data["object"]
    metadata = stripe_sub.get("metadata", {})
    if metadata.get("client_id"):
        is_active = stripe_sub["status"] == "active"
        if is_active:
            client_subscription_service.activate_client_agent(
                stripe_sub["id"],
                stripe_sub.get("customer", ""),
                metadata["client_id"],
                metadata.get("agent_slug", "linkedin"),
                stripe_sub["status"],
            )
        else:
            client_subscription_service.deactivate_client_agent(
                stripe_sub["id"],
                stripe_sub["status"],
            )
    else:
        subscription_service.handle_subscription_updated(data)


def _handle_subscription_deleted(data: dict) -> None:
    stripe_sub = data["object"]
    metadata = stripe_sub.get("metadata", {})
    if metadata.get("client_id"):
        client_subscription_service.deactivate_client_agent(
            stripe_sub["id"],
            "canceled",
        )
    else:
        subscription_service.handle_subscription_deleted(data)


def _handle_invoice_payment_failed(data: dict) -> None:
    invoice = data["object"]
    stripe_sub_id = invoice.get("subscription")
    if not stripe_sub_id:
        return

    # Try client path first (check if subscription has client_id metadata)
    handled = client_subscription_service.deactivate_client_agent_by_stripe_id(
        stripe_sub_id, "past_due"
    )
    if not handled:
        subscription_service.handle_invoice_payment_failed(data)


HANDLED_EVENTS = {
    "customer.subscription.created": _handle_subscription_created,
    "customer.subscription.updated": _handle_subscription_updated,
    "customer.subscription.deleted": _handle_subscription_deleted,
    "invoice.payment_failed": _handle_invoice_payment_failed,
}


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="stripe-signature"),
):
    """Handle incoming Stripe webhook events."""
    payload = await request.body()
    event = stripe_service.construct_webhook_event(payload, stripe_signature)

    handler = HANDLED_EVENTS.get(event["type"])
    if handler:
        logger.info("Processing Stripe event: %s", event["type"])
        handler(event["data"])
    else:
        logger.debug("Ignoring unhandled Stripe event: %s", event["type"])

    return {"success": True, "data": {"received": True}}
