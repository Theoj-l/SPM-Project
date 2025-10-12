"""Authentication service for Supabase integration."""

from typing import Optional, Dict, Any
from app.supabase_client import get_supabase_client
from app.config import settings


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
        
        Args:
            access_token: The access token
            
        Returns:
            User information dictionary or None if invalid token
        """
        try:
            supabase = get_supabase_client()
            
            # Set the session for the client
            supabase.auth.set_session(access_token, "")
            
            # Get user
            user = supabase.auth.get_user()
            
            if user:
                return {
                    "id": user.id,
                    "email": user.email,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                    "email_confirmed_at": user.email_confirmed_at,
                    "last_sign_in_at": user.last_sign_in_at,
                    "app_metadata": user.app_metadata,
                    "user_metadata": user.user_metadata,
                }
            
            return None
            
        except Exception as e:
            print(f"Get user error: {str(e)}")
            return None
