"""Health check router."""

from fastapi import APIRouter
from app.models.base import HealthResponse
from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        service=settings.title,
        version=settings.version
    )
