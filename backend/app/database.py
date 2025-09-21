"""Database configuration and setup for Supabase."""

from app.supabase_client import get_supabase_client

def get_supabase():
    """Dependency to get Supabase client."""
    return get_supabase_client()
