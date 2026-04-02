"""Stripe service — checkout sessions and webhook processing."""

from __future__ import annotations

import logging

import stripe

from app.config import settings
from app.exceptions import ValidationError

logger = logging.getLogger(__name__)

stripe.api_key = settings.stripe_secret_key


def create_checkout_session(
    user_id: str,
    user_email: str,
    user_agent_id: str,
    template_name: str,
    price_id: str | None = None,
) -> str:
    """Create a Stripe Checkout session and return the URL."""
    checkout_price = price_id or settings.stripe_price_id

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            customer_email=user_email,
            line_items=[{"price": checkout_price, "quantity": 1}],
            metadata={
                "user_id": user_id,
                "user_agent_id": user_agent_id,
                "template_name": template_name,
            },
            success_url=f"{settings.frontend_url}/dashboard?hired=true",
            cancel_url=f"{settings.frontend_url}/marketplace",
        )
        if not session or not session.url:
            raise ValidationError("Failed to create checkout session")
        return session.url
    except stripe.error.StripeError as e:
        logger.error(f"Stripe checkout error: {e}")
        raise ValidationError(f"Payment error: {getattr(e, 'user_message', str(e))}")


def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify and construct a Stripe webhook event."""
    try:
        return stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise ValidationError("Invalid Stripe webhook signature")
    except ValueError:
        raise ValidationError("Invalid webhook payload")


def cancel_subscription(stripe_subscription_id: str, at_period_end: bool = True) -> stripe.Subscription:
    """Cancel a Stripe subscription."""
    try:
        return stripe.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=at_period_end,
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe cancel error: {e}")
        raise ValidationError(f"Failed to cancel subscription: {getattr(e, 'user_message', str(e))}")


def reactivate_subscription(stripe_subscription_id: str) -> stripe.Subscription:
    """Reactivate a cancelled-at-period-end subscription."""
    try:
        return stripe.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=False,
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe reactivate error: {e}")
        raise ValidationError(f"Failed to reactivate subscription: {getattr(e, 'user_message', str(e))}")
