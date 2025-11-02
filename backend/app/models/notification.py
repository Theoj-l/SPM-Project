from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from datetime import datetime

class NotificationOut(BaseModel):
    id: str
    user_id: str
    type: Literal["task_update", "mention", "task_assigned", "deadline_reminder", "overdue", "daily_digest"]
    title: str
    message: str
    read: bool
    created_at: str
    link_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # Store additional data like task_id, comment_id, etc.

class NotificationCreate(BaseModel):
    user_id: str
    type: Literal["task_update", "mention", "task_assigned", "deadline_reminder", "overdue", "daily_digest"]
    title: str
    message: str
    link_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

