"""LinkedIn API v2 client.

Handles profile fetch and post creation via ugcPosts.
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_LINKEDIN_API = "https://api.linkedin.com/v2"
_LINKEDIN_USERINFO = "https://api.linkedin.com/v2/userinfo"


def get_profile(access_token: str) -> dict:
    """Fetch LinkedIn profile using OpenID Connect userinfo endpoint."""
    resp = httpx.get(
        _LINKEDIN_USERINFO,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10.0,
    )
    resp.raise_for_status()
    return resp.json()


def create_post(access_token: str, person_urn: str, text: str) -> dict:
    """Create a LinkedIn post. Returns dict with post_urn."""
    payload = {
        "author": f"urn:li:person:{person_urn}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }
    resp = httpx.post(
        f"{_LINKEDIN_API}/ugcPosts",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        },
        json=payload,
        timeout=15.0,
    )
    resp.raise_for_status()
    post_urn = resp.headers.get("x-restli-id", "")
    return {"post_urn": post_urn, "status": resp.status_code}
