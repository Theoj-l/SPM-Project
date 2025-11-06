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
    
    @staticmethod
    def get_or_create_user(user_id: str, email: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user by ID, or create if doesn't exist.
        
        Args:
            user_id: User's ID from Supabase auth
            email: User's email address
            display_name: User's display name (optional)
            
        Returns:
            User information dictionary
        """
        try:
            # First try to get by ID
            result = SupabaseService.select("users", "*", {"id": user_id})
            if result and len(result) > 0:
                return result[0]
            
            # If not found, try by email
            result = SupabaseService.select("users", "*", {"email": email})
            if result and len(result) > 0:
                return result[0]
            
            # User doesn't exist, create it
            user_data = {
                "id": user_id,
                "email": email,
                "roles": ["staff"],  # Default role
            }
            if display_name:
                user_data["display_name"] = display_name
            
            created_user = SupabaseService.insert("users", user_data)
            print(f"Created new user in database: {email}")
            return created_user
            
        except Exception as e:
            print(f"Get or create user error: {str(e)}")
            # If creation fails, try to get by email one more time (race condition)
            result = SupabaseService.select("users", "*", {"email": email})
            if result and len(result) > 0:
                return result[0]
            raise