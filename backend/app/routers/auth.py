"""Authentication router for user login and registration."""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.base import BaseResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    refresh_token: str
    user: dict
    expires_in: int


class RegisterRequest(BaseModel):
    """Registration request model."""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


@router.post("/login", response_model=BaseResponse)
async def login(request: LoginRequest):
    """
    Authenticate user with email and password.
    
    Returns:
        - access_token: JWT token for API authentication
        - refresh_token: Token for refreshing access token
        - user: User information
        - expires_in: Token expiration time in seconds
    """
    try:
        result = AuthService.login(request.email, request.password)
        
        if not result:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        return BaseResponse(
            success=True,
            message="Login successful",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/register", response_model=BaseResponse)
async def register(request: RegisterRequest):
    """
    Register a new user.
    
    Returns:
        - access_token: JWT token for API authentication
        - refresh_token: Token for refreshing access token
        - user: User information
        - expires_in: Token expiration time in seconds
    """
    try:
        result = AuthService.register(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        if not result:
            raise HTTPException(
                status_code=400,
                detail="Registration failed"
            )
        
        return BaseResponse(
            success=True,
            message="Registration successful",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/logout", response_model=BaseResponse)
async def logout():
    """
    Logout user (invalidate tokens).
    
    Note: This is a placeholder endpoint. In a real implementation,
    you would invalidate the tokens on the server side.
    """
    return BaseResponse(
        success=True,
        message="Logout successful",
        data={}
    )


@router.post("/refresh", response_model=BaseResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    
    Returns:
        - access_token: New JWT token for API authentication
        - refresh_token: New refresh token
        - expires_in: Token expiration time in seconds
    """
    try:
        result = AuthService.refresh_token(request.refresh_token)
        
        if not result:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )
        
        return BaseResponse(
            success=True,
            message="Token refreshed successfully",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.get("/me", response_model=BaseResponse)
async def get_current_user(authorization: str = Header(None)):
    """
    Get current user information.
    
    Args:
        authorization: Bearer token from Authorization header
    """
    try:
        print(f"Authorization header: {authorization}")
        
        if not authorization or not authorization.startswith("Bearer "):
            print("Missing or invalid authorization header")
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid authorization header"
            )
        
        access_token = authorization.split(" ")[1]
        print(f"Access token: {access_token[:20]}...")
        
        user_data = AuthService.get_user(access_token)
        print(f"User data: {user_data}")
        
        if not user_data:
            print("No user data returned from AuthService")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
        return BaseResponse(
            success=True,
            message="User information retrieved successfully",
            data=user_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user information: {str(e)}"
        )


@router.get("/user-roles", response_model=BaseResponse)
async def get_user_roles(authorization: str = Header(None)):
    """
    Get user roles by email from the users table.
    
    Args:
        authorization: Bearer token from Authorization header
    """
    try:
        print(f"Getting user roles - Authorization header: {authorization}")
        
        if not authorization or not authorization.startswith("Bearer "):
            print("Missing or invalid authorization header")
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid authorization header"
            )
        
        access_token = authorization.split(" ")[1]
        print(f"Access token: {access_token[:20]}...")
        
        # Get user info from token
        user_data = AuthService.get_user(access_token)
        if not user_data:
            print("No user data returned from AuthService")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
        user_email = user_data.get("email")
        if not user_email:
            print("No email found in user data")
            raise HTTPException(
                status_code=400,
                detail="User email not found"
            )
        
        print(f"Getting roles for user: {user_email}")
        
        # Get user with roles from users table
        user_with_roles = UserService.get_user_with_roles(user_email)
        
        if not user_with_roles:
            print(f"No user found in users table for email: {user_email}")
            # Return default staff role if user not found in users table
            user_with_roles = {
                "email": user_email,
                "roles": ["staff"]
            }
        
        print(f"User roles data: {user_with_roles}")
        
        return BaseResponse(
            success=True,
            message="User roles retrieved successfully",
            data=user_with_roles
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_user_roles: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user roles: {str(e)}"
        )
