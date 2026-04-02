"""FastAPI dependencies — auth middleware chain."""

import logging

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db.connection import get_anon_client, get_service_client
from app.exceptions import ForbiddenError, NotFoundError, UnauthorizedError

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Extract and verify Supabase JWT. Returns user_id (UUID string)."""
    token = credentials.credentials
    anon = get_anon_client()

    try:
        user_response = anon.auth.get_user(token)
        if user_response is None or user_response.user is None:
            raise UnauthorizedError()
        return user_response.user.id
    except UnauthorizedError:
        raise
    except (AttributeError, TypeError, ValueError) as e:
        logger.warning(f"Token verification failed: {e}")
        raise UnauthorizedError()


async def get_current_user(user_id: str = Depends(verify_token)) -> dict:
    """Fetch profile from DB using verified user_id."""
    db = get_service_client()
    result = (
        db.table("profiles")
        .select("*")
        .eq("id", user_id)
        .is_("deleted_at", "null")
        .single()
        .execute()
    )

    if not result.data:
        raise NotFoundError("User profile not found")

    return result.data


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Ensure the current user is an admin."""
    if not current_user.get("is_admin"):
        raise ForbiddenError("Admin access required")
    return current_user
