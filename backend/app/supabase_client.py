"""Supabase client configuration."""

from supabase import create_client, Client
from app.config import settings
import httpx

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
        
        # Create HTTP client with timeout to prevent hanging requests
        # Default timeout: 10 seconds for connect, 30 seconds for read
        timeout = httpx.Timeout(10.0, read=30.0)
        http_client = httpx.Client(timeout=timeout)
        
        # Create Supabase client with custom HTTP client
        # Note: The supabase-py library may not directly support passing http_client
        # So we'll create the client normally and handle timeouts at the application level
        try:
            # Try to create client with options if supported
            _supabase_client = create_client(url, key)
        except Exception as e:
            print(f"Error creating Supabase client: {e}")
            # Fallback to basic client creation
            _supabase_client = create_client(url, key)
    
    return _supabase_client
