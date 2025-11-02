"""Notification service for managing in-app notifications."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.supabase_client import get_supabase_client
from app.models.notification import NotificationOut, NotificationCreate
import uuid

class NotificationService:
    """Service for managing notifications."""
    
    def __init__(self):
        self.client = get_supabase_client()
    
    def create_notification(self, notification_data: NotificationCreate) -> Optional[NotificationOut]:
        """Create a new notification."""
        try:
            notification_id = str(uuid.uuid4())
            notification_record = {
                "id": notification_id,
                "user_id": notification_data.user_id,
                "type": notification_data.type,
                "title": notification_data.title,
                "message": notification_data.message,
                "read": False,
                "link_url": notification_data.link_url,
                "metadata": notification_data.metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("notifications").insert(notification_record).execute()
            
            if result.data:
                return NotificationOut(
                    id=notification_id,
                    user_id=notification_data.user_id,
                    type=notification_data.type,
                    title=notification_data.title,
                    message=notification_data.message,
                    read=False,
                    created_at=notification_record["created_at"],
                    link_url=notification_data.link_url,
                    metadata=notification_data.metadata
                )
            return None
        except Exception as e:
            print(f"Error creating notification: {e}")
            return None
    
    def get_user_notifications(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0,
        include_read: bool = True
    ) -> List[NotificationOut]:
        """Get notifications for a user with pagination."""
        try:
            query = self.client.table("notifications").select("*").eq("user_id", user_id)
            
            if not include_read:
                query = query.eq("read", False)
            
            query = query.order("created_at", desc=True).limit(limit).offset(offset)
            
            result = query.execute()
            
            notifications = []
            for notif_data in result.data:
                notifications.append(NotificationOut(
                    id=notif_data["id"],
                    user_id=notif_data["user_id"],
                    type=notif_data["type"],
                    title=notif_data["title"],
                    message=notif_data["message"],
                    read=notif_data.get("read", False),
                    created_at=notif_data["created_at"],
                    link_url=notif_data.get("link_url"),
                    metadata=notif_data.get("metadata", {})
                ))
            
            return notifications
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []
    
    def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read."""
        try:
            result = self.client.table("notifications").update({"read": True}).eq("id", notification_id).eq("user_id", user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False
    
    def mark_all_as_read(self, user_id: str) -> bool:
        """Mark all notifications as read for a user."""
        try:
            result = self.client.table("notifications").update({"read": True}).eq("user_id", user_id).eq("read", False).execute()
            return True
        except Exception as e:
            print(f"Error marking all notifications as read: {e}")
            return False
    
    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user."""
        try:
            result = self.client.table("notifications").select("id", count="exact").eq("user_id", user_id).eq("read", False).execute()
            return result.count or 0
        except Exception as e:
            print(f"Error getting unread count: {e}")
            return 0
    
    def create_task_update_notification(
        self, 
        user_id: str, 
        task_id: str, 
        task_title: str, 
        old_status: str, 
        new_status: str,
        project_id: Optional[str] = None
    ) -> Optional[NotificationOut]:
        """Create a notification for task status change."""
        link_url = f"/projects/{project_id}/tasks/{task_id}" if project_id else f"/tasks/{task_id}"
        
        return self.create_notification(NotificationCreate(
            user_id=user_id,
            type="task_update",
            title="Task Status Updated",
            message=f"Task '{task_title}' status changed from {old_status} to {new_status}",
            link_url=link_url,
            metadata={
                "task_id": task_id,
                "project_id": project_id,
                "old_status": old_status,
                "new_status": new_status
            }
        ))
    
    def create_mention_notification(
        self,
        mentioned_user_id: str,
        commenter_user_id: str,
        commenter_name: str,
        task_id: str,
        task_title: str,
        comment_preview: str,
        project_id: Optional[str] = None
    ) -> Optional[NotificationOut]:
        """Create a notification when user is mentioned."""
        link_url = f"/projects/{project_id}/tasks/{task_id}" if project_id else f"/tasks/{task_id}"
        
        return self.create_notification(NotificationCreate(
            user_id=mentioned_user_id,
            type="mention",
            title="You were mentioned",
            message=f"{commenter_name} mentioned you in a comment on task '{task_title}': {comment_preview[:100]}",
            link_url=link_url,
            metadata={
                "task_id": task_id,
                "project_id": project_id,
                "commenter_user_id": commenter_user_id,
                "comment_preview": comment_preview
            }
        ))
    
    def create_task_assigned_notification(
        self,
        user_id: str,
        task_id: str,
        task_title: str,
        project_id: Optional[str] = None
    ) -> Optional[NotificationOut]:
        """Create a notification when task is assigned."""
        link_url = f"/projects/{project_id}/tasks/{task_id}" if project_id else f"/tasks/{task_id}"
        
        return self.create_notification(NotificationCreate(
            user_id=user_id,
            type="task_assigned",
            title="New Task Assigned",
            message=f"You have been assigned to task '{task_title}'",
            link_url=link_url,
            metadata={
                "task_id": task_id,
                "project_id": project_id
            }
        ))

