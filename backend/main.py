"""Main application entry point."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.routers import health, api_router
from app.routers import tasks
from app.middleware import LoggingMiddleware

# Create FastAPI app
app = FastAPI(
    title=settings.title,
    description=settings.description,
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)

# Include routers
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(api_router, prefix=settings.api_prefix)  # ✅ includes tasks router


# Add Supabase router conditionally to avoid import errors
try:
    from app.routers import supabase
    app.include_router(supabase.router, prefix=settings.api_prefix)
    print("✅ Supabase router loaded successfully")
except Exception as e:
    print(f"⚠️ Supabase router failed to load: {e}")
    print("Supabase endpoints will not be available")

# items.router will be added when frontend needs item functionality

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"{settings.title} is running",
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
