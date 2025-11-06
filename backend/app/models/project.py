from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, List
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, description="Project name")
    cover_url: Optional[str] = None

class ProjectOut(BaseModel):
    id: str
    name: str
    owner_id: str
    owner_display_name: Optional[str] = None
    cover_url: Optional[str] = None
    user_role: Optional[str] = None
    status: Literal["active", "archived"] = "active"

class TaskCreate(BaseModel):
    title: str = Field(min_length=1)
    description: Optional[str] = None
    due_date: Optional[str] = Field(None, description="Due date and time in YYYY-MM-DD HH:MM:SS format")
    notes: Optional[str] = None
    assignee_ids: Optional[List[str]] = Field(default_factory=list, max_items=5, description="Optional additional assignees. Creator will be added as default assignee.")
    status: Literal["todo", "in_progress", "completed", "blocked"] = "todo"
    type: Literal["active", "archived"] = "active"
    recurring: Optional[dict] = None  # Used only for creation - expands into multiple individual tasks, not stored in DB
    tags: Optional[str] = Field(None, description="Tags as free text separated by # (e.g., 'urgent#bug#frontend')")
    priority: Optional[int] = Field(None, ge=1, le=10, description="Priority level from 1 (lowest) to 10 (highest)")
    
    @validator('tags')
    def parse_tags(cls, v):
        """Parse tags from free text input separated by #"""
        if not v:
            return []
        # Split by #, trim whitespace, filter empty strings
        parsed = [tag.strip() for tag in str(v).split('#') if tag.strip()]
        if len(parsed) > 10:  # Reasonable limit
            raise ValueError('Maximum 10 tags allowed')
        return parsed
    
    @validator('due_date')
    def validate_due_date(cls, v):
        if v:
            try:
                from datetime import datetime
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError('Invalid date format, must be YYYY-MM-DD')
        return v
    
    @validator('recurring')
    def validate_recurring(cls, v):
        if v and v.get('enabled'):
            # If recurring is enabled, end_date is required (no infinite recurring)
            if not v.get('end_date'):
                raise ValueError('End date is required for recurring tasks')
            # Validate end_date format
            try:
                from datetime import datetime
                datetime.strptime(v['end_date'], "%Y-%m-%d")
            except ValueError:
                raise ValueError('Invalid recurring end_date format, must be YYYY-MM-DD')
            except KeyError:
                raise ValueError('End date is required for recurring tasks')
        return v

class TaskReassign(BaseModel):
    new_project_id: Optional[str]  # allow None for 'standalone' if needed

class TaskUpdate(BaseModel):
    """Model for updating tasks - tags can be updated, project cannot"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["todo", "in_progress", "completed", "blocked"]] = None
    notes: Optional[str] = None
    assignee_ids: Optional[List[str]] = Field(None, max_items=5, description="Updating assignees. All assignees can add, only managers can remove.")
    tags: Optional[str] = Field(None, description="Tags as free text separated by # (e.g., 'urgent#bug#frontend')")
    priority: Optional[int] = Field(None, ge=1, le=10, description="Priority level from 1 (lowest) to 10 (highest)")
    
    @validator('tags')
    def parse_tags(cls, v):
        """Parse tags from free text input separated by #"""
        if not v:
            return None  # None means don't update tags
        # Split by #, trim whitespace, filter empty strings
        parsed = [tag.strip() for tag in str(v).split('#') if tag.strip()]
        if len(parsed) > 10:  # Reasonable limit
            raise ValueError('Maximum 10 tags allowed')
        return parsed

class TaskAssigneeUpdate(BaseModel):
    assignee_ids: List[str] = Field(min_items=1, max_items=5, description="At least one assignee is required")
    
    @validator('assignee_ids')
    def validate_assignee_count(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one assignee is required')
        if len(v) > 5:
            raise ValueError('Maximum 5 assignees allowed')
        return v

class TaskOut(BaseModel):
    id: str
    project_id: Optional[str]
    title: str
    description: Optional[str] = None
    status: Literal["todo","in_progress","completed","blocked"] = "todo"
    due_date: Optional[str] = Field(None, description="Due date and time in YYYY-MM-DD HH:MM:SS format")
    notes: Optional[str] = None
    assignee_ids: Optional[List[str]] = Field(default_factory=list)
    assignee_names: Optional[List[str]] = Field(default_factory=list)  # For display purposes
    type: Literal["active", "archived"] = "active"
    tags: Optional[List[str]] = Field(default_factory=list)
    priority: Optional[int] = Field(None, ge=1, le=10, description="Priority level from 1 (lowest) to 10 (highest)")
    created_at: Optional[str] = None

class ProjectMemberAdd(BaseModel):
    email: str = Field(description="Email of the user to add")
    role: str = Field(default="member", description="Role in the project (owner, manager, member)")

class ProjectMemberOut(BaseModel):
    project_id: str
    user_id: str
    role: str
    user_email: Optional[str] = None
    user_display_name: Optional[str] = None

# Comment models
class CommentCreate(BaseModel):
    content: str = Field(min_length=1, description="Comment content")
    task_id: str = Field(description="Task ID this comment belongs to")
    parent_comment_id: Optional[str] = Field(None, description="Parent comment ID for sub-comments")

class CommentOut(BaseModel):
    id: str
    task_id: str
    user_id: str
    parent_comment_id: Optional[str] = None
    content: str
    created_at: str
    user_email: Optional[str] = None
    user_display_name: Optional[str] = None
    replies: Optional[List['CommentOut']] = Field(default_factory=list)  # For nested comments

# Sub-task models
class SubTaskCreate(BaseModel):
    title: str = Field(min_length=1, description="Sub-task title")
    description: Optional[str] = None
    parent_task_id: str = Field(description="Parent task ID")
    status: Literal["todo", "in_progress", "completed", "blocked"] = "todo"
    assignee_ids: List[str] = Field(min_items=1, max_items=5, description="At least one assignee is required")
    due_date: Optional[str] = Field(None, description="Due date and time in YYYY-MM-DD HH:MM:SS format")
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: Optional[List[str]] = Field(default_factory=list, max_items=5)
    priority: Optional[int] = Field(None, ge=1, le=10, description="Priority level from 1 (lowest) to 10 (highest)")

class SubTaskOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    parent_task_id: str
    status: Literal["todo", "in_progress", "completed", "blocked"] = "todo"
    assignee_ids: Optional[List[str]] = Field(default_factory=list)
    assignee_names: Optional[List[str]] = Field(default_factory=list)
    due_date: Optional[str] = Field(None, description="Due date and time in YYYY-MM-DD HH:MM:SS format")
    notes: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    priority: Optional[int] = Field(None, ge=1, le=10, description="Priority level from 1 (lowest) to 10 (highest)")
    created_at: Optional[str] = None

# File models
class FileUpload(BaseModel):
    filename: str = Field(description="Original filename")
    content_type: str = Field(description="MIME type")
    file_size: int = Field(description="File size in bytes")
    task_id: str = Field(description="Task ID this file belongs to")
    
    @validator('file_size')
    def validate_file_size(cls, v):
        max_size = 50 * 1024 * 1024  # 50MB
        if v > max_size:
            raise ValueError('File size cannot exceed 50MB')
        return v

class FileOut(BaseModel):
    id: str
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    task_id: Optional[str] = None
    subtask_id: Optional[str] = None
    uploaded_by: str
    created_at: str
    download_url: Optional[str] = None
    uploader_email: Optional[str] = None
    uploader_display_name: Optional[str] = None