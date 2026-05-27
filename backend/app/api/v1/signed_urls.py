"""HMAC-signed URL helper for modelUrl and download links."""
from __future__ import annotations

import hashlib
import hmac
import time
from urllib.parse import urlencode

from app.api.v1.errors import V1Error
from app.config import settings


def _secret() -> bytes:
    key = settings.model_url_signing_key
    if not key:
        raise RuntimeError("MODEL_URL_SIGNING_KEY is not set")
    return key.encode()


def sign_url(path: str, job_id: str, ttl_minutes: int | None = None) -> str:
    """Return a signed URL path with ?sig=...&exp=... query params."""
    ttl = (ttl_minutes or settings.signed_url_ttl_minutes) * 60
    exp = int(time.time()) + ttl
    payload = f"{path}:{job_id}:{exp}"
    sig = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{path}?{urlencode({'job_id': job_id, 'exp': exp, 'sig': sig})}"


def verify_signed_url(path: str, job_id: str, exp: str, sig: str) -> None:
    """Raise V1Error(401) if the signature is invalid or the URL has expired."""
    try:
        exp_int = int(exp)
    except (ValueError, TypeError):
        raise V1Error(401, "INVALID_SIGNATURE", "Malformed signed URL")

    if int(time.time()) > exp_int:
        raise V1Error(401, "LINK_EXPIRED", "Signed URL has expired")

    payload = f"{path}:{job_id}:{exp}"
    expected = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise V1Error(401, "INVALID_SIGNATURE", "Signature mismatch")
