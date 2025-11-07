"""Supabase client configuration."""

from supabase import create_client, Client
from supabase.client import ClientOptions
from app.config import settings
import httpx

_supabase_client: Client = None

def get_supabase_client() -> Client:
    """Get Supabase client instance (lazy initialization). Uses service role key to bypass RLS.
    
    The client is a singleton, which means connection pooling happens automatically at the httpx level.
    The supabase-py library creates its own httpx.Client internally with connection pooling enabled.
    """
    global _supabase_client
    
    if _supabase_client is None:
        # Try both naming conventions
        url = settings.supabase_url or settings.SUPABASE_URL
        # Use service role key for backend operations (bypasses RLS)
        key = settings.supabase_service_key or settings.SUPABASE_SERVICE_KEY or settings.supabase_key or settings.SUPABASE_KEY
        
        if not url or not key:
            raise ValueError("Supabase URL and key must be set in environment variables")
        
        # Create Supabase client with optimized timeouts
        # The supabase-py library uses httpx internally with connection pooling enabled by default
        # We configure timeouts to prevent hanging requests
        try:
            options = ClientOptions(
                auto_refresh_token=False,  # We handle token refresh manually
                persist_session=False,  # Don't persist sessions in backend
                postgrest_client_timeout=httpx.Timeout(10.0, read=30.0, connect=5.0),  # Optimized timeouts for PostgREST
                storage_client_timeout=httpx.Timeout(20.0, read=60.0, connect=5.0)  # Longer timeout for storage operations
            )
            _supabase_client = create_client(url, key, options)
        except Exception as e:
            print(f"Error creating Supabase client with options: {e}")
            # Fallback: try without options (older API)
            try:
                _supabase_client = create_client(url, key)
            except Exception as e2:
                print(f"Error creating Supabase client: {e2}")
                raise
    
    return _supabase_client
