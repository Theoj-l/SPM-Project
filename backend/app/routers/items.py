"""Items router - Only health check for now."""

from fastapi import APIRouter

router = APIRouter(prefix="/items", tags=["items"])

# Placeholder for future item endpoints
# Add only what the frontend actually needs
