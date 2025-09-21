"""Supabase client configuration."""

from supabase import create_client, Client
from app.config import settings

_supabase_client: Client = None

def get_supabase_client() -> Client:
    """Get Supabase client instance (lazy initialization)."""
    global _supabase_client
    
    if _supabase_client is None:
        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError("Supabase URL and key must be set in environment variables")
        
        _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
    
    return _supabase_client

# Note: Service key is only needed for admin operations
# For most use cases, the anon key is sufficient
