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
    due_date: Optional[str] = None
    notes: Optional[str] = None
    assignee_ids: Optional[List[str]] = Field(default_factory=list, max_items=5)
    status: Literal["todo", "in_progress", "completed", "blocked"] = "todo"
    type: Literal["active", "archived"] = "active"
    recurring: Optional[dict] = None  # Store recurring configuration as JSON
    tags: Optional[List[str]] = Field(default_factory=list, max_items=5)
    
    @validator('assignee_ids')
    def validate_assignee_count(cls, v):
        if v and len(v) > 5:
            raise ValueError('Maximum 5 assignees allowed')
        return v or []
    
    @validator('tags')
    def validate_tags_count(cls, v):
        if v and len(v) > 5:
            raise ValueError('Maximum 5 tags allowed')
        return v or []
    
    @validator('due_date')
    def validate_due_date(cls, v):
        if v:
            try:
                from datetime import datetime
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError('Invalid date format, must be YYYY-MM-DD')
        return v

class TaskReassign(BaseModel):
    new_project_id: Optional[str]  # allow None for 'standalone' if needed

class TaskAssigneeUpdate(BaseModel):
    assignee_ids: List[str] = Field(max_items=5)
    
    @validator('assignee_ids')
    def validate_assignee_count(cls, v):
        if len(v) > 5:
            raise ValueError('Maximum 5 assignees allowed')
        return v

class TaskOut(BaseModel):
    id: str
    project_id: Optional[str]
    title: str
    description: Optional[str] = None
    status: Literal["todo","in_progress","completed","blocked"] = "todo"
    due_date: Optional[str] = None
    notes: Optional[str] = None
    assignee_ids: Optional[List[str]] = Field(default_factory=list)
    assignee_names: Optional[List[str]] = Field(default_factory=list)  # For display purposes
    type: Literal["active", "archived"] = "active"
    tags: Optional[List[str]] = Field(default_factory=list)
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
    assignee_ids: Optional[List[str]] = Field(default_factory=list, max_items=5)
    tags: Optional[List[str]] = Field(default_factory=list, max_items=5)

class SubTaskOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    parent_task_id: str
    status: Literal["todo", "in_progress", "completed", "blocked"] = "todo"
    assignee_ids: Optional[List[str]] = Field(default_factory=list)
    assignee_names: Optional[List[str]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)
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
    task_id: str
    uploaded_by: str
    created_at: str
    download_url: Optional[str] = None
    uploader_email: Optional[str] = None
    uploader_display_name: Optional[str] = None