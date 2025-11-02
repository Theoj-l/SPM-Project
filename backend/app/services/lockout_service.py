"""Service for handling account lockouts and failed login attempts."""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from app.services.supabase_service import SupabaseService


class LockoutService:
    """Service class for account lockout operations."""
    
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    
    @staticmethod
    def get_client_ip(request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded IP (from proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client IP
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    @staticmethod
    def check_lockout(email: str) -> Optional[Dict[str, Any]]:
        """
        Check if account is currently locked.
        
        Args:
            email: User's email address
            
        Returns:
            Dict with lockout info if locked, None if not locked
        """
        try:
            lockouts = SupabaseService.select(
                "account_lockouts",
                "*",
                {"email": email}
            )
            
            if not lockouts or len(lockouts) == 0:
                return None
            
            lockout = lockouts[0]
            locked_until_str = lockout.get("locked_until")
            
            if not locked_until_str:
                # No lockout period set
                return None
            
            # Parse locked_until datetime
            try:
                # Try parsing ISO format
                if isinstance(locked_until_str, str):
                    # Handle different datetime formats
                    locked_until_str = locked_until_str.replace('Z', '+00:00')
                    if '+' not in locked_until_str and '-' in locked_until_str[-6:]:
                        # Already has timezone
                        pass
                    locked_until = datetime.fromisoformat(locked_until_str)
                else:
                    # If it's already a datetime object (from database)
                    locked_until = locked_until_str
                
                if locked_until.tzinfo is None:
                    # Assume UTC if no timezone
                    locked_until = locked_until.replace(tzinfo=timezone.utc)
                
                now = datetime.now(locked_until.tzinfo)
            except (ValueError, AttributeError) as e:
                print(f"Error parsing lockout datetime: {str(e)}")
                return None
            
            if now < locked_until:
                # Still locked
                remaining_seconds = int((locked_until - now).total_seconds())
                return {
                    "locked": True,
                    "locked_until": locked_until.isoformat(),
                    "remaining_seconds": remaining_seconds,
                    "remaining_minutes": max(1, remaining_seconds // 60)
                }
            else:
                # Lockout expired, clean it up
                SupabaseService.delete("account_lockouts", {"email": email})
                # Also reset failed attempts
                SupabaseService.delete("failed_login_attempts", {"email": email})
                return None
            
        except Exception as e:
            print(f"Check lockout error: {str(e)}")
            return None
    
    @staticmethod
    def record_failed_attempt(email: str, ip_address: str) -> Dict[str, Any]:
        """
        Record a failed login attempt.
        
        Args:
            email: User's email address
            ip_address: IP address of the login attempt
            
        Returns:
            Dict with lockout status
        """
        try:
            # Get existing failed attempts
            attempts = SupabaseService.select(
                "failed_login_attempts",
                "*",
                {"email": email}
            )
            
            current_count = 0
            attempt_id = None
            
            if attempts and len(attempts) > 0:
                attempt = attempts[0]
                current_count = attempt.get("failed_count", 0)
                attempt_id = attempt.get("id")
            
            new_count = current_count + 1
            
            # Update or create failed attempts record
            attempt_data = {
                "email": email,
                "failed_count": new_count,
                "last_attempt_at": datetime.utcnow().isoformat(),
                "last_attempt_ip": ip_address
            }
            
            if attempt_id:
                SupabaseService.update(
                    "failed_login_attempts",
                    attempt_data,
                    {"id": attempt_id}
                )
            else:
                SupabaseService.insert("failed_login_attempts", attempt_data)
            
            # Check if we've reached max attempts
            if new_count >= LockoutService.MAX_FAILED_ATTEMPTS:
                # Lock the account
                locked_until = datetime.utcnow() + timedelta(minutes=LockoutService.LOCKOUT_DURATION_MINUTES)
                
                lockout_data = {
                    "email": email,
                    "locked_until": locked_until.isoformat(),
                    "locked_at": datetime.utcnow().isoformat(),
                    "lockout_reason": "max_failed_attempts"
                }
                
                # Update or create lockout record
                existing_lockouts = SupabaseService.select(
                    "account_lockouts",
                    "*",
                    {"email": email}
                )
                
                if existing_lockouts and len(existing_lockouts) > 0:
                    SupabaseService.update(
                        "account_lockouts",
                        lockout_data,
                        {"email": email}
                    )
                else:
                    SupabaseService.insert("account_lockouts", lockout_data)
                
                return {
                    "locked": True,
                    "failed_count": new_count,
                    "locked_until": locked_until.isoformat(),
                    "remaining_seconds": LockoutService.LOCKOUT_DURATION_MINUTES * 60
                }
            
            return {
                "locked": False,
                "failed_count": new_count,
                "remaining_attempts": LockoutService.MAX_FAILED_ATTEMPTS - new_count
            }
            
        except Exception as e:
            print(f"Record failed attempt error: {str(e)}")
            return {"locked": False, "failed_count": 0}
    
    @staticmethod
    def reset_failed_attempts(email: str):
        """
        Reset failed login attempts counter (on successful login).
        
        Args:
            email: User's email address
        """
        try:
            SupabaseService.delete("failed_login_attempts", {"email": email})
        except Exception as e:
            print(f"Reset failed attempts error: {str(e)}")
    
    @staticmethod
    def unlock_account(email: str, unlocked_by: Optional[str] = None) -> bool:
        """
        Manually unlock an account (admin action).
        
        Args:
            email: User's email address
            unlocked_by: Email of admin who unlocked it
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove lockout
            SupabaseService.delete("account_lockouts", {"email": email})
            
            # Reset failed attempts
            SupabaseService.delete("failed_login_attempts", {"email": email})
            
            return True
        except Exception as e:
            print(f"Unlock account error: {str(e)}")
            return False
    

