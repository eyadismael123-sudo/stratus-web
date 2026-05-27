"""GET /v1/health"""
from __future__ import annotations

import time

from fastapi import APIRouter

from app.api.v1.schemas import HealthResponse

router = APIRouter()

_START = time.time()
_VERSION = "1.0.0"


@router.get("/health", response_model=HealthResponse, tags=["v1"])
async def health() -> HealthResponse:
    return HealthResponse(version=_VERSION, uptime_seconds=round(time.time() - _START, 1))
