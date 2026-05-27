"""v1 error envelope — {error: {code, message, details}}.

Scoped to /v1 routes only; does not affect the existing Stratus error handler.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class V1Error(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: dict | None = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


async def v1_error_handler(request: Request, exc: V1Error) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )


# ── Common factory helpers ─────────────────────────────────────────────────────

def unauthorized(message: str = "Invalid or missing API key") -> V1Error:
    return V1Error(401, "UNAUTHORIZED", message)


def bad_request(message: str, details: dict | None = None) -> V1Error:
    return V1Error(400, "BAD_REQUEST", message, details)


def not_found(resource: str) -> V1Error:
    return V1Error(404, "NOT_FOUND", f"{resource} not found")


def rate_limited(retry_after: int = 60) -> V1Error:
    return V1Error(429, "RATE_LIMITED", "Too many requests", {"retry_after_seconds": retry_after})


def internal(message: str = "Internal server error") -> V1Error:
    return V1Error(500, "INTERNAL_ERROR", message)
