"""Supabase client configuration."""

from supabase import create_client, Client
from app.config import settings

_supabase_client: Client = None

def get_supabase_client() -> Client:
    """Get Supabase client instance (lazy initialization). Uses service role key to bypass RLS."""
    global _supabase_client
    
    if _supabase_client is None:
        # Try both naming conventions
        url = settings.supabase_url or settings.SUPABASE_URL
        # Use service role key for backend operations (bypasses RLS)
        key = settings.supabase_service_key or settings.SUPABASE_SERVICE_KEY or settings.supabase_key or settings.SUPABASE_KEY
        
        if not url or not key:
            raise ValueError("Supabase URL and key must be set in environment variables")
        
        _supabase_client = create_client(url, key)
    
    return _supabase_client
