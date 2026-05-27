"""X-API-Key + X-App-Stage validation for all /v1 routes."""
from __future__ import annotations

from typing import Annotated

from fastapi import Header, Security
from fastapi.security import APIKeyHeader

from app.api.v1.errors import V1Error, unauthorized, bad_request
from app.config import settings

_api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)
_VALID_STAGES = {"staging", "production"}


def _valid_keys() -> frozenset[str]:
    raw = settings.print3d_api_keys.strip()
    if not raw:
        return frozenset()
    return frozenset(k.strip() for k in raw.split(",") if k.strip())


async def require_api_key(
    x_api_key: Annotated[str | None, Security(_api_key_scheme)] = None,
) -> str:
    if not x_api_key or x_api_key not in _valid_keys():
        raise unauthorized()
    return x_api_key


async def require_app_stage(
    x_app_stage: Annotated[str | None, Header(alias="X-App-Stage")] = None,
) -> str:
    if not x_app_stage or x_app_stage not in _VALID_STAGES:
        raise bad_request(
            "X-App-Stage header is required",
            {"allowed_values": list(_VALID_STAGES)},
        )
    return x_app_stage
