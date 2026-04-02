"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """Simple health check."""
    return {"success": True, "data": {"status": "healthy"}}
