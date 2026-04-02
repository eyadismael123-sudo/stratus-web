"""User/profile schemas — matches web/types/index.ts Profile."""

from __future__ import annotations

from pydantic import BaseModel


class ProfileResponse(BaseModel):
    """Matches frontend Profile interface exactly."""

    id: str
    email: str
    full_name: str | None = None
    company_name: str | None = None
    avatar_url: str | None = None
    timezone: str = "UTC"
    is_admin: bool = False
    created_at: str
    updated_at: str


class UpdateProfileRequest(BaseModel):
    """Matches frontend UpdateProfilePayload."""

    full_name: str | None = None
    company_name: str | None = None
    timezone: str | None = None
    notification_email: str | None = None
