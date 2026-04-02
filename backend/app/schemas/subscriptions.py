"""Subscription schemas — matches web/types/index.ts Subscription."""

from __future__ import annotations

from pydantic import BaseModel


class SubscriptionResponse(BaseModel):
    """Matches frontend Subscription interface."""

    id: str
    user_id: str
    user_agent_id: str
    stripe_subscription_id: str
    stripe_customer_id: str
    stripe_price_id: str
    status: str
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool = False
    canceled_at: str | None = None
    amount_usd_cents: int
    billing_interval: str = "month"
    created_at: str


class CancelSubscriptionRequest(BaseModel):
    """Request body for POST /subscriptions/{id}/cancel."""

    reason: str | None = None
    feedback: str | None = None
