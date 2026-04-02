"""Auth service — profile operations."""

from app.exceptions import NotFoundError
from app.repositories import profiles as profile_repo


def get_profile(user_id: str) -> dict:
    """Fetch user profile or raise NotFoundError."""
    profile = profile_repo.get_profile_by_id(user_id)
    if not profile:
        raise NotFoundError("Profile not found")
    return profile


def update_profile(user_id: str, updates: dict) -> dict:
    """Update profile fields and return updated profile."""
    updated = profile_repo.update_profile(user_id, updates)
    if not updated:
        raise NotFoundError("Profile not found")
    return updated
