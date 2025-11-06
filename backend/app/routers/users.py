"""User management router."""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List, Dict, Any
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.supabase_service import SupabaseService

router = APIRouter(prefix="/users", tags=["users"])

# Get current user from JWT token
def get_current_user_id(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    access_token = authorization.split(" ")[1]
    user_data = AuthService.get_user(access_token)
    if not user_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    user_email = user_data.get("email")
    user_id_from_token = user_data.get("id")
    if not user_email:
        raise HTTPException(
            status_code=400,
            detail="User email not found"
        )
    if not user_id_from_token:
        raise HTTPException(
            status_code=400,
            detail="User ID not found in token"
        )
    
    # Get or create user in users table
    display_name = user_data.get("user_metadata", {}).get("full_name") or user_data.get("user_metadata", {}).get("display_name")
    user = UserService.get_or_create_user(user_id_from_token, user_email, display_name)
    
    return user["id"]

@router.get("", response_model=List[Dict[str, Any]])
def list_users(authorization: str = Header(None)):
    """
    List all users in the system.
    Only accessible by managers and admins.
    """
    # Get current user info
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    access_token = authorization.split(" ")[1]
    user_data = AuthService.get_user(access_token)
    if not user_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    user_email = user_data.get("email")
    if not user_email:
        raise HTTPException(
            status_code=400,
            detail="User email not found"
        )
    
    # Check if current user is manager or admin
    user_id_from_token = user_data.get("id")
    display_name = user_data.get("user_metadata", {}).get("full_name") or user_data.get("user_metadata", {}).get("display_name")
    current_user = UserService.get_or_create_user(user_id_from_token, user_email, display_name)
    
    user_roles = current_user.get("roles", [])
    if not any(role in ["manager", "admin"] for role in user_roles):
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only managers and admins can list users"
        )
    
    # Get all users
    users = SupabaseService.select("users", "*")
    
    # Return user data without sensitive information
    return [
        {
            "id": user["id"],
            "email": user["email"],
            "display_name": user.get("display_name"),
            "roles": user.get("roles", [])
        }
        for user in users
    ]

@router.get("/search", response_model=List[Dict[str, Any]])
def search_users(query: str, authorization: str = Header(None)):
    """
    Search users by email or display name.
    Only accessible by managers and admins.
    """
    # Get current user info
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    access_token = authorization.split(" ")[1]
    user_data = AuthService.get_user(access_token)
    if not user_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    user_email = user_data.get("email")
    if not user_email:
        raise HTTPException(
            status_code=400,
            detail="User email not found"
        )
    
    # Check if current user is manager or admin
    user_id_from_token = user_data.get("id")
    display_name = user_data.get("user_metadata", {}).get("full_name") or user_data.get("user_metadata", {}).get("display_name")
    current_user = UserService.get_or_create_user(user_id_from_token, user_email, display_name)
    
    user_roles = current_user.get("roles", [])
    if not any(role in ["manager", "admin"] for role in user_roles):
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only managers and admins can search users"
        )
    
    if not query or len(query.strip()) < 2:
        raise HTTPException(
            status_code=400,
            detail="Search query must be at least 2 characters"
        )
    
    # Search users by email or display name
    # Use ilike filter for case-insensitive search
    client = SupabaseService.get_client()
    result = client.table("users").select("*").ilike("email", f"%{query}%").execute()
    
    users = result.data or []
    
    # Also search by display_name if not found by email
    if not users:
        result = client.table("users").select("*").ilike("display_name", f"%{query}%").execute()
        users = result.data or []
    
    # Return user data without sensitive information
    return [
        {
            "id": user["id"],
            "email": user["email"],
            "display_name": user.get("display_name"),
            "roles": user.get("roles", [])
        }
        for user in users
    ]
