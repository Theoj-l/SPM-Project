"""Tasks router."""

from fastapi import APIRouter
from app.services import tasks  # import your service module

# Create router instance for tasks
router = APIRouter(tags=["tasks"])
router.include_router(tasks.router)

# Include all routes from the service
router.include_router(tasks.router)
