"""Webhook endpoints — Stripe event processing."""

import logging

from fastapi import APIRouter, Header, Request

from app.services import stripe_service, subscription_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

HANDLED_EVENTS = {
    "customer.subscription.created": subscription_service.handle_subscription_created,
    "customer.subscription.updated": subscription_service.handle_subscription_updated,
    "customer.subscription.deleted": subscription_service.handle_subscription_deleted,
    "invoice.payment_failed": subscription_service.handle_invoice_payment_failed,
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
        logger.info(f"Processing Stripe event: {event['type']}")
        handler(event["data"])
    else:
        logger.debug(f"Ignoring unhandled Stripe event: {event['type']}")

    return {"success": True, "data": {"received": True}}
