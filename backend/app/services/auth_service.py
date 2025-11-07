"""Authentication service for Supabase integration."""

from typing import Optional, Dict, Any
from app.supabase_client import get_supabase_client
from app.config import settings
import time

# Simple in-memory cache for user data (token -> user_data, expires after 5 minutes)
_user_cache: Dict[str, tuple] = {}  # {token: (user_data, expiry_timestamp)}
_cache_ttl = 300  # 5 minutes in seconds


class AuthService:
    """Service class for authentication operations using Supabase."""
    
    @staticmethod
    def login(email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary containing access_token, refresh_token, user info, and expires_in
            None if authentication fails
        """
        try:
            supabase = get_supabase_client()
            
            # Sign in with email and password
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                return {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "created_at": response.user.created_at,
                        "updated_at": response.user.updated_at,
                        "email_confirmed_at": response.user.email_confirmed_at,
                        "last_sign_in_at": response.user.last_sign_in_at,
                        "app_metadata": response.user.app_metadata,
                        "user_metadata": response.user.user_metadata,
                    },
                    "expires_in": response.session.expires_in,
                    "expires_at": response.session.expires_at,
                    "token_type": response.session.token_type
                }
            
            return None
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            return None
    
    @staticmethod
    def register(email: str, password: str, full_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Register a new user.
        
        Args:
            email: User's email address
            password: User's password
            full_name: User's full name (optional)
            
        Returns:
            Dictionary containing access_token, refresh_token, user info, and expires_in
            None if registration fails
        """
        try:
            supabase = get_supabase_client()
            
            # Prepare user metadata
            user_metadata = {}
            if full_name:
                user_metadata["full_name"] = full_name
            
            # Sign up with email and password
            response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata
                }
            })
            
            if response.user and response.session:
                return {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "created_at": response.user.created_at,
                        "updated_at": response.user.updated_at,
                        "email_confirmed_at": response.user.email_confirmed_at,
                        "last_sign_in_at": response.user.last_sign_in_at,
                        "app_metadata": response.user.app_metadata,
                        "user_metadata": response.user.user_metadata,
                    },
                    "expires_in": response.session.expires_in,
                    "expires_at": response.session.expires_at,
                    "token_type": response.session.token_type
                }
            elif response.user and not response.session:
                # User created but needs email confirmation
                return {
                    "message": "User created successfully. Please check your email for confirmation.",
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "created_at": response.user.created_at,
                        "email_confirmed_at": response.user.email_confirmed_at,
                    },
                    "requires_confirmation": True
                }
            
            return None
            
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return None
    
    @staticmethod
    def refresh_token(refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            Dictionary containing new access_token and refresh_token
            None if refresh fails
        """
        try:
            supabase = get_supabase_client()
            
            response = supabase.auth.refresh_session(refresh_token)
            
            if response.session:
                return {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_in": response.session.expires_in,
                    "expires_at": response.session.expires_at,
                    "token_type": response.session.token_type
                }
            
            return None
            
        except Exception as e:
            print(f"Token refresh error: {str(e)}")
            return None
    
    @staticmethod
    def logout(access_token: str) -> bool:
        """
        Logout user by invalidating the session.
        
        Args:
            access_token: The access token to invalidate
            
        Returns:
            True if logout successful, False otherwise
        """
        try:
            supabase = get_supabase_client()
            
            # Set the session for the client
            supabase.auth.set_session(access_token, "")
            
            # Sign out
            supabase.auth.sign_out()
            
            return True
            
        except Exception as e:
            print(f"Logout error: {str(e)}")
            return False
    
    @staticmethod
    def get_user(access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from access token.
        Uses caching to reduce API calls and prevent timeouts.
        
        Args:
            access_token: The access token
            
        Returns:
            User information dictionary or None if invalid token
        """
        global _user_cache
        
        # Check cache first
        current_time = time.time()
        if access_token in _user_cache:
            user_data, expiry = _user_cache[access_token]
            if current_time < expiry:
                return user_data
            else:
                # Cache expired, remove it
                del _user_cache[access_token]
        
        max_retries = 2
        retry_delay = 0.5  # seconds
        
        for attempt in range(max_retries + 1):
            try:
                supabase = get_supabase_client()
                
                # Get user with the access token
                response = supabase.auth.get_user(access_token)
                
                if response and response.user:
                    user_data = {
                        "id": response.user.id,
                        "email": response.user.email,
                        "created_at": response.user.created_at,
                        "updated_at": response.user.updated_at,
                        "email_confirmed_at": response.user.email_confirmed_at,
                        "last_sign_in_at": response.user.last_sign_in_at,
                        "app_metadata": response.user.app_metadata,
                        "user_metadata": response.user.user_metadata,
                    }
                    
                    # Cache the result
                    _user_cache[access_token] = (user_data, current_time + _cache_ttl)
                    
                    # Clean up expired cache entries (keep cache size manageable)
                    if len(_user_cache) > 100:
                        _user_cache = {
                            k: v for k, v in _user_cache.items() 
                            if v[1] > current_time
                        }
                    
                    return user_data
                
                return None
                
            except Exception as e:
                error_str = str(e).lower()
                # Check if it's a timeout error
                is_timeout = (
                    "timeout" in error_str or 
                    "timed out" in error_str or
                    "read operation timed out" in error_str
                )
                
                if is_timeout and attempt < max_retries:
                    print(f"Get user timeout (attempt {attempt + 1}/{max_retries + 1}), retrying...")
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    print(f"Get user error: {str(e)}")
                    # On final failure, check if we have a cached value (even if expired)
                    # This provides some resilience during Supabase outages
                    if access_token in _user_cache:
                        cached_data, _ = _user_cache[access_token]
                        print("Returning cached user data due to timeout")
                        return cached_data
                    return None
        
        return None
    
    @staticmethod
    def reset_password_for_email(email: str, redirect_url: Optional[str] = None) -> bool:
        """
        Send password reset email to user.
        
        Args:
            email: User's email address
            redirect_url: Optional redirect URL for the password reset link
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            import json
            from urllib.request import Request, urlopen
            from urllib.parse import urlencode
            
            # Get Supabase URL and key from settings
            supabase_url = settings.supabase_url or settings.SUPABASE_URL
            supabase_key = settings.supabase_key or settings.SUPABASE_KEY
            
            if not supabase_url or not supabase_key:
                print("Supabase URL or key not configured")
                return False
            
            # Default redirect URL if not provided
            if not redirect_url:
                redirect_url = f"{settings.frontend_url or 'http://localhost:3000'}/reset-password"
            
            # Make direct HTTP request to Supabase Auth API
            auth_url = f"{supabase_url.rstrip('/')}/auth/v1/recover?{urlencode({'redirect_to': redirect_url})}"
            
            data = json.dumps({"email": email}).encode('utf-8')
            req = Request(
                auth_url,
                data=data,
                headers={
                    "apikey": supabase_key,
                    "Content-Type": "application/json",
                },
                method="POST"
            )
            
            try:
                with urlopen(req) as response:
                    status_code = response.getcode()
                    # Supabase returns 200 even if email doesn't exist (security feature)
                    if status_code in [200, 204]:
                        return True
                    else:
                        response_text = response.read().decode('utf-8')
                        print(f"Password reset API error: {status_code} - {response_text}")
                        return False
            except Exception as http_error:
                # urllib raises HTTPError for non-2xx status codes
                error_body = http_error.read().decode('utf-8') if hasattr(http_error, 'read') else str(http_error)
                print(f"Password reset HTTP error: {error_body}")
                return False
            
        except Exception as e:
            print(f"Password reset error: {str(e)}")
            return False
    
    @staticmethod
    def update_password_with_token(access_token: str, new_password: str) -> bool:
        """
        Update user password using a recovery token.
        For Supabase, we need to first exchange the recovery token for a session,
        then update the password with that session.
        
        Args:
            access_token: The access token from the password reset link
            new_password: The new password
            
        Returns:
            True if password updated successfully, False otherwise
        """
        try:
            import json
            from urllib.request import Request, urlopen
            
            # Get Supabase URL and key from settings
            supabase_url = settings.supabase_url or settings.SUPABASE_URL
            supabase_key = settings.supabase_key or settings.SUPABASE_KEY
            
            if not supabase_url or not supabase_key:
                print("Supabase URL or key not configured")
                return False
            
            # Step 1: Exchange recovery token for a session token
            # Supabase requires us to verify/exchange the recovery token first
            token_exchange_url = f"{supabase_url.rstrip('/')}/auth/v1/token?grant_type=password"
            
            exchange_data = json.dumps({
                "email": "",  # Not needed for recovery token exchange
                "password": "",  # Not needed for recovery token exchange
            }).encode('utf-8')
            
            # First, try to get user info with the recovery token to verify it's valid
            user_url = f"{supabase_url.rstrip('/')}/auth/v1/user"
            user_req = Request(
                user_url,
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                method="GET"
            )
            
            try:
                # Verify the token works by getting user info
                with urlopen(user_req) as user_response:
                    user_status = user_response.getcode()
                    if user_status not in [200]:
                        user_text = user_response.read().decode('utf-8')
                        print(f"Token verification failed: {user_status} - {user_text}")
                        return False
                    
                    # Token is valid, now update password
                    update_data = json.dumps({"password": new_password}).encode('utf-8')
                    update_req = Request(
                        user_url,
                        data=update_data,
                        headers={
                            "apikey": supabase_key,
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json",
                        },
                        method="PUT"
                    )
                    
                    with urlopen(update_req) as update_response:
                        update_status = update_response.getcode()
                        if update_status in [200, 204]:
                            print("Password updated successfully")
                            return True
                        else:
                            update_text = update_response.read().decode('utf-8')
                            print(f"Password update API error: {update_status} - {update_text}")
                            return False
                            
            except Exception as http_error:
                error_body = http_error.read().decode('utf-8') if hasattr(http_error, 'read') else str(http_error)
                print(f"Password update HTTP error: {error_body}")
                return False
            
        except Exception as e:
            print(f"Password update error: {str(e)}")
            return False