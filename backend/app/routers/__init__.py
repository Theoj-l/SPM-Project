# API routers package
from fastapi import APIRouter
from .health import router as health_router
from .items import router as items_router
from .supabase import router as supabase_router
from .projects import router as projects_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(items_router)
api_router.include_router(supabase_router)
api_router.include_router(projects_router)
