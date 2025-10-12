from pydantic import BaseModel, Field
from typing import Optional, Literal

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, description="Project name")
    cover_url: Optional[str] = None

class ProjectOut(BaseModel):
    id: str
    name: str
    owner_id: str
    cover_url: Optional[str] = None

class TaskCreate(BaseModel):
    title: str = Field(min_length=1)
    assignee_id: Optional[str] = None

class TaskReassign(BaseModel):
    new_project_id: Optional[str]  # allow None for 'standalone' if needed

class TaskOut(BaseModel):
    id: str
    project_id: Optional[str]
    title: str
    status: Literal["todo","in_progress","review","done"] = "todo"
    assignee_id: Optional[str] = None
