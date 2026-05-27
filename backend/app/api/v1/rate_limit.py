"""Per-customer_id rate limiting using slowapi."""
from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def _key_by_customer_id(request: Request) -> str:
    # Form fields aren't parsed yet at middleware level, so fall back to IP.
    # The per-route decorators extract customer_id from the parsed body after
    # auth passes; this keyfunc is used for the global limiter default only.
    return get_remote_address(request)


limiter = Limiter(key_func=_key_by_customer_id)


def customer_limit(request: Request, customer_id: str) -> str:
    """Key function that binds the rate limit to the authenticated customer_id."""
    return f"customer:{customer_id}"


def rate_limit_str() -> str:
    return f"{settings.rate_limit_per_minute}/minute"
