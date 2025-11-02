"""Notification router for managing notifications."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.models.notification import NotificationOut
from app.services.notification_service import NotificationService
from app.routers.projects import get_current_user_id

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/", response_model=List[NotificationOut])
async def get_notifications(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_read: bool = Query(True)
):
    """Get notifications for the current user."""
    try:
        notification_service = NotificationService()
        notifications = notification_service.get_user_notifications(
            user_id=user_id,
            limit=limit,
            offset=offset,
            include_read=include_read
        )
        return notifications
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unread-count")
async def get_unread_count(user_id: str = Depends(get_current_user_id)):
    """Get count of unread notifications."""
    try:
        notification_service = NotificationService()
        count = notification_service.get_unread_count(user_id)
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Mark a notification as read."""
    try:
        notification_service = NotificationService()
        success = notification_service.mark_as_read(notification_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/mark-all-read")
async def mark_all_as_read(user_id: str = Depends(get_current_user_id)):
    """Mark all notifications as read for the current user."""
    try:
        notification_service = NotificationService()
        notification_service.mark_all_as_read(user_id)
        return {"message": "All notifications marked as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

