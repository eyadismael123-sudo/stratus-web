"""Subscription endpoints — billing management."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.schemas.subscriptions import CancelSubscriptionRequest, SubscriptionResponse
from app.services import subscription_service

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("", response_model=SuccessResponse[list[SubscriptionResponse]])
def list_subscriptions(current_user: dict = Depends(get_current_user)):
    """List all subscriptions for the current user."""
    subs = subscription_service.list_subscriptions(current_user["id"])
    return {"success": True, "data": subs}


@router.post("/{subscription_id}/cancel", response_model=SuccessResponse[SubscriptionResponse])
def cancel_subscription(
    subscription_id: str,
    body: CancelSubscriptionRequest | None = None,
    current_user: dict = Depends(get_current_user),
):
    """Cancel a subscription at period end."""
    reason = body.reason if body else None
    updated = subscription_service.cancel_subscription(
        subscription_id, current_user["id"], reason
    )
    return {"success": True, "data": updated}


@router.post("/{subscription_id}/reactivate", response_model=SuccessResponse[SubscriptionResponse])
def reactivate_subscription(
    subscription_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Reactivate a subscription scheduled for cancellation."""
    updated = subscription_service.reactivate_subscription(
        subscription_id, current_user["id"]
    )
    return {"success": True, "data": updated}
