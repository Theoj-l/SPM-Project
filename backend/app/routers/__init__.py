# API routers package
from fastapi import APIRouter
from .health import router as health_router
from .items import router as items_router
from .supabase import router as supabase_router
from .projects import router as projects_router
from .auth import router as auth_router
from .users import router as users_router
from .tasks import router as tasks_router
from .teams import router as teams_router
from .notifications import router as notifications_router
from .test_email import router as test_email_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(items_router)
api_router.include_router(supabase_router)
api_router.include_router(projects_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(teams_router, prefix="/teams", tags=["teams"])
api_router.include_router(notifications_router)
api_router.include_router(test_email_router)
