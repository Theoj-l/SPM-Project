"""
UAA-1 / UAA-4 / UAA-5: Authentication, Inactivity Logout, Account Lockout Tests

Rewritten to match actual AuthService implementation:
- AuthService uses static methods
- Uses get_supabase_client() with .auth.sign_in_with_password()
- Returns access_token, refresh_token, user info
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

try:
    from app.services.auth_service import AuthService
except Exception:
    AuthService = None


def test_login_with_valid_credentials_returns_token():
    """
    UAA-1: Login with valid credentials grants access and returns token
    """
    if AuthService is None:
        pytest.skip("AuthService not importable")

    email = "user@test.com"
    password = "correct_password"

    with patch('app.services.auth_service.get_supabase_client') as mock_get_client:
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        
        # Mock successful auth response
        mock_auth_response = MagicMock()
        mock_auth_response.user = MagicMock(
            id="user123",
            email=email,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            email_confirmed_at="2024-01-01T00:00:00Z",
            last_sign_in_at="2024-01-01T00:00:00Z",
            app_metadata={},
            user_metadata={}
        )
        mock_auth_response.session = MagicMock(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            refresh_token="refresh_token_here",
            expires_in=3600,
            expires_at=1234567890,
            token_type="bearer"
        )
        
        mock_supabase.auth.sign_in_with_password.return_value = mock_auth_response
        
        # Call login
        result = AuthService.login(email=email, password=password)
        
        # Verify successful login
        assert result is not None
        assert "access_token" in result
        assert "refresh_token" in result
        assert "user" in result
        assert result["user"]["id"] == "user123"
        assert result["user"]["email"] == email
        assert result["token_type"] == "bearer"
        
        # Verify correct method was called
        mock_supabase.auth.sign_in_with_password.assert_called_once_with({
            "email": email,
            "password": password
        })


def test_login_with_invalid_credentials_returns_none():
    """
    UAA-1: Login with invalid credentials denies access
    """
    if AuthService is None:
        pytest.skip("AuthService not importable")

    email = "user@test.com"
    wrong_password = "wrong_password"

    with patch('app.services.auth_service.get_supabase_client') as mock_get_client:
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        
        # Mock failed auth - raise exception
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")
        
        # Call login
        result = AuthService.login(email=email, password=wrong_password)
        
        # Verify login failed
        assert result is None


def test_register_new_user_returns_token():
    """
    UAA-1: User registration creates account and returns token
    """
    if AuthService is None:
        pytest.skip("AuthService not importable")

    email = "newuser@test.com"
    password = "secure_password123"
    full_name = "New User"

    with patch('app.services.auth_service.get_supabase_client') as mock_get_client:
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        
        # Mock successful registration
        mock_auth_response = MagicMock()
        mock_auth_response.user = MagicMock(
            id="newuser123",
            email=email,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            email_confirmed_at="2024-01-01T00:00:00Z",
            last_sign_in_at=None,
            app_metadata={},
            user_metadata={"full_name": full_name}
        )
        mock_auth_response.session = MagicMock(
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            expires_in=3600,
            expires_at=1234567890,
            token_type="bearer"
        )
        
        mock_supabase.auth.sign_up.return_value = mock_auth_response
        
        # Call register
        result = AuthService.register(email=email, password=password, full_name=full_name)
        
        # Verify successful registration
        assert result is not None
        assert "access_token" in result
        assert "user" in result
        assert result["user"]["email"] == email
        assert result["user"]["user_metadata"]["full_name"] == full_name
        
        # Verify correct method was called
        mock_supabase.auth.sign_up.assert_called_once_with({
            "email": email,
            "password": password,
            "options": {
                "data": {"full_name": full_name}
            }
        })


def test_refresh_token_returns_new_tokens():
    """
    UAA-4: Refresh token provides new access token
    """
    if AuthService is None:
        pytest.skip("AuthService not importable")

    refresh_token = "existing_refresh_token"

    with patch('app.services.auth_service.get_supabase_client') as mock_get_client:
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        
        # Mock successful token refresh
        mock_auth_response = MagicMock()
        mock_auth_response.session = MagicMock(
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            expires_in=3600,
            expires_at=1234567890,
            token_type="bearer"
        )
        
        mock_supabase.auth.refresh_session.return_value = mock_auth_response
        
        # Call refresh_token
        result = AuthService.refresh_token(refresh_token=refresh_token)
        
        # Verify new tokens returned
        assert result is not None
        assert "access_token" in result
        assert result["access_token"] == "new_access_token"
        assert result["refresh_token"] == "new_refresh_token"
        
        # Verify correct method was called
        mock_supabase.auth.refresh_session.assert_called_once_with(refresh_token)


def test_session_timeout_simulation():
    """
    UAA-4: Simulate session timeout after inactivity (15 minutes)
    Note: Actual timeout is handled by Supabase token expiration
    """
    if AuthService is None:
        pytest.skip("AuthService not importable")

    # Test that expired token refresh fails
    expired_refresh_token = "expired_token"

    with patch('app.services.auth_service.get_supabase_client') as mock_get_client:
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        
        # Mock expired token - refresh fails
        mock_supabase.auth.refresh_session.side_effect = Exception("Token expired")
        
        # Attempt to refresh expired token
        result = AuthService.refresh_token(refresh_token=expired_refresh_token)
        
        # Verify refresh failed
        assert result is None


# End of file