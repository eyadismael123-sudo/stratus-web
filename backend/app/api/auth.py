"""Auth endpoints — profile management."""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.schemas.users import ProfileResponse, UpdateProfileRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/profile", response_model=SuccessResponse[ProfileResponse])
def get_profile(current_user: dict = Depends(get_current_user)):
    """Fetch the current user's profile."""
    return {"success": True, "data": current_user}


@router.patch("/profile", response_model=SuccessResponse[ProfileResponse])
def update_profile(
    body: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update the current user's profile."""
    updates = body.model_dump(exclude_unset=True)
    updated = auth_service.update_profile(current_user["id"], updates)
    return {"success": True, "data": updated}
