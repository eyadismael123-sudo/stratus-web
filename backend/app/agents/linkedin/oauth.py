"""LinkedIn OAuth2 authorization code flow.

Scopes: openid profile email w_member_social

Auth: https://www.linkedin.com/oauth/v2/authorization
Token: https://www.linkedin.com/oauth/v2/accessToken
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_AUTH_BASE = "https://www.linkedin.com/oauth/v2/authorization"
_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
_SCOPES = "openid profile email w_member_social"


def generate_auth_url(client_id: str) -> tuple[str, str]:
    """Generate LinkedIn OAuth URL and a state token.

    State is embedded as "{client_id}:{random}" so the callback can recover
    which Stratus client completed the OAuth flow.

    Returns (auth_url, state_token).
    """
    random_part = secrets.token_urlsafe(24)
    state = f"{client_id}:{random_part}"
    params = {
        "response_type": "code",
        "client_id": settings.linkedin_client_id,
        "redirect_uri": settings.linkedin_redirect_uri,
        "scope": _SCOPES,
        "state": state,
    }
    return f"{_AUTH_BASE}?{urlencode(params)}", state


def exchange_code(code: str) -> dict:
    """Exchange authorization code for tokens.

    Returns dict: access_token, refresh_token (may be absent), expires_at (ISO).
    """
    resp = httpx.post(
        _TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.linkedin_redirect_uri,
            "client_id": settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 5183944))
    return {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token"),
        "expires_at": expires_at.isoformat(),
    }


def refresh_access_token(refresh_token: str) -> dict:
    """Use refresh_token to get a new access token."""
    resp = httpx.post(
        _TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 5183944))
    return {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token", refresh_token),
        "expires_at": expires_at.isoformat(),
    }
