"""Supabase test router."""

from fastapi import APIRouter, HTTPException
from app.models.base import BaseResponse

router = APIRouter(prefix="/supabase", tags=["supabase"])


@router.get("/")
async def supabase_info():
    """Supabase router info."""
    return {"message": "Supabase router is working", "endpoints": ["/test"]}


@router.get("/test")
async def test_supabase():
    """Test Supabase connection by fetching from test table."""
    try:
        # First test: Check if Supabase credentials are set
        from app.config import settings
        
        if not settings.supabase_url or not settings.supabase_key:
            return BaseResponse(
                success=False,
                message="Supabase credentials not configured",
                data={"error": "Please set SUPABASE_URL and SUPABASE_KEY in .env file"}
            )
        
        # Second test: Try to import and use Supabase service
        from app.services.supabase_service import SupabaseService
        
        # Get record with id = 1 from test table
        result = SupabaseService.select("test", "*", {"id": 1})
        
        if not result:
            return BaseResponse(
                success=False,
                message="No record found with id=1 in test table",
                data={"error": "Create a test table with id=1 record"}
            )
        
        return BaseResponse(
            success=True,
            message="Supabase connection successful",
            data=result[0]  # Return the first (and should be only) record
        )
        
    except Exception as e:
        return BaseResponse(
            success=False,
            message="Supabase test failed",
            data={"error": str(e)}
        )
