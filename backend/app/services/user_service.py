"""User service for user-related operations."""

from typing import Optional, Dict, Any, List
from app.services.supabase_service import SupabaseService


class UserService:
    """Service class for user operations."""
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """
        Get user information by email from the users table.
        
        Args:
            email: User's email address
            
        Returns:
            User information dictionary or None if not found
        """
        try:
            # Query the users table by email
            result = SupabaseService.select("users", "*", {"email": email})
            
            if result and len(result) > 0:
                return result[0]  # Return the first (and should be only) user
            
            return None
            
        except Exception as e:
            print(f"Get user by email error: {str(e)}")
            return None
    
    @staticmethod
    def get_user_roles(email: str) -> List[str]:
        """
        Get user roles by email from the users table.
        
        Args:
            email: User's email address
            
        Returns:
            List of role names (staff, manager, admin)
        """
        try:
            user = UserService.get_user_by_email(email)
            
            if user and "roles" in user:
                roles = user["roles"]
                if isinstance(roles, list):
                    return roles
                elif isinstance(roles, str):
                    # Handle case where roles might be stored as comma-separated string
                    return [role.strip() for role in roles.split(",")]
            
            return ["staff"]  # Default to staff role
            
        except Exception as e:
            print(f"Get user roles error: {str(e)}")
            return ["staff"]
    
    @staticmethod
    def has_role(email: str, role_name: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            email: User's email address
            role_name: Role name to check (staff, manager, admin)
            
        Returns:
            True if user has the role, False otherwise
        """
        try:
            user_roles = UserService.get_user_roles(email)
            return role_name in user_roles
        except Exception as e:
            print(f"Check user role error: {str(e)}")
            return False
    
    @staticmethod
    def get_user_with_roles(email: str) -> Optional[Dict[str, Any]]:
        """
        Get user information with roles.
        
        Args:
            email: User's email address
            
        Returns:
            User information dictionary with roles or None if not found
        """
        try:
            user = UserService.get_user_by_email(email)
            
            if user:
                # Just return the roles as they are from the database
                roles = user.get("roles", ["staff"])  # Default to staff if no roles
                user["roles"] = roles
                
                return user
            
            return None
            
        except Exception as e:
            print(f"Get user with roles error: {str(e)}")
            return None
