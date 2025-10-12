"""Authentication router for user login and registration."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.base import BaseResponse
from app.services.auth_service import AuthService

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


@router.get("/me", response_model=BaseResponse)
async def get_current_user():
    """
    Get current user information.
    
    Note: This endpoint would require authentication middleware
    to extract user information from the JWT token.
    """
    return BaseResponse(
        success=True,
        message="User information endpoint",
        data={"note": "This endpoint requires authentication middleware"}
    )
