"""Subscription repository — Supabase queries for billing records."""

from __future__ import annotations

from app.db.connection import get_service_client


def list_user_subscriptions(user_id: str) -> list[dict]:
    """List all subscriptions for a user."""
    db = get_service_client()
    result = (
        db.table("subscriptions")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


def get_subscription_by_id(subscription_id: str, user_id: str) -> dict | None:
    """Fetch a single subscription (ownership enforced)."""
    db = get_service_client()
    result = (
        db.table("subscriptions")
        .select("*")
        .eq("id", subscription_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    return result.data


def get_subscription_by_stripe_id(stripe_subscription_id: str) -> dict | None:
    """Fetch subscription by Stripe subscription ID (for webhooks)."""
    db = get_service_client()
    result = (
        db.table("subscriptions")
        .select("*")
        .eq("stripe_subscription_id", stripe_subscription_id)
        .single()
        .execute()
    )
    return result.data


def create_subscription(data: dict) -> dict:
    """Create a new subscription record."""
    db = get_service_client()
    result = db.table("subscriptions").insert(data).execute()
    if not result.data:
        raise ValueError("Failed to create subscription")
    return result.data[0]


def update_subscription(subscription_id: str, updates: dict) -> dict | None:
    """Update a subscription record."""
    filtered = {k: v for k, v in updates.items() if v is not None}
    if not filtered:
        return None

    db = get_service_client()
    result = (
        db.table("subscriptions")
        .update(filtered)
        .eq("id", subscription_id)
        .execute()
    )
    return result.data[0] if result.data else None


def update_subscription_by_stripe_id(
    stripe_subscription_id: str, updates: dict
) -> dict | None:
    """Update subscription by Stripe ID (for webhooks)."""
    filtered = {k: v for k, v in updates.items() if v is not None}
    if not filtered:
        return None

    db = get_service_client()
    result = (
        db.table("subscriptions")
        .update(filtered)
        .eq("stripe_subscription_id", stripe_subscription_id)
        .execute()
    )
    return result.data[0] if result.data else None
