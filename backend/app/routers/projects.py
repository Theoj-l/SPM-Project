print("✅ Loaded projects.py router file")

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict
from app.models.project import ProjectCreate, ProjectOut
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])

# Dummy auth dependency — replace with your real auth (e.g., JWT -> user_id)
def get_current_user_id() -> str:
    # In production use: decode token / session
    # Here we accept "x-user-id" header from a reverse proxy or Next.js fetch
    return "11111111-1111-1111-1111-111111111111"

@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, user_id: str = Depends(get_current_user_id)):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Project name is required.")
    return ProjectService.create_project(name=payload.name, owner_id=user_id, cover_url=payload.cover_url)

@router.get("", response_model=List[ProjectOut])
def list_my_projects(user_id: str = Depends(get_current_user_id)):
    return ProjectService.list_for_user(user_id)

# @router.post("/{project_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
# def add_task(project_id: str, payload: TaskCreate, user_id: str = Depends(get_current_user_id)):
#     # Optionally: check manager role in project_members first
#     return ProjectService.add_task(project_id=project_id, title=payload.title, assignee_id=payload.assignee_id)

# @router.patch("/tasks/{task_id}/reassign", response_model=TaskOut)
# def reassign_task(task_id: str, payload: TaskReassign, user_id: str = Depends(get_current_user_id)):
#     return ProjectService.reassign_task(task_id, payload.new_project_id)

# @router.get("/{project_id}/kanban")
# def kanban(project_id: str, user_id: str = Depends(get_current_user_id)) -> Dict[str, list]:
#     return ProjectService.tasks_grouped_kanban(project_id)
