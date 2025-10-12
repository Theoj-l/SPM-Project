print("✅ Loaded projects.py router file")

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import List, Dict, Optional
from app.models.project import ProjectCreate, ProjectOut, ProjectMemberAdd, ProjectMemberOut
from app.services.project_service import ProjectService
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/projects", tags=["projects"])

# Get current user from JWT token
def get_current_user_id(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    access_token = authorization.split(" ")[1]
    user_data = AuthService.get_user(access_token)
    if not user_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    user_email = user_data.get("email")
    if not user_email:
        raise HTTPException(
            status_code=400,
            detail="User email not found"
        )
    
    # Get user ID from users table
    user = UserService.get_user_by_email(user_email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    return user["id"]

@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, user_id: str = Depends(get_current_user_id)):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Project name is required.")
    return ProjectService.create_project(name=payload.name, owner_id=user_id, cover_url=payload.cover_url)

@router.get("", response_model=List[ProjectOut])
def list_my_projects(user_id: str = Depends(get_current_user_id)):
    return ProjectService.list_for_user(user_id)

@router.delete("/{project_id}")
def delete_project(project_id: str, user_id: str = Depends(get_current_user_id)):
    # Check if user is the owner of the project
    if not ProjectService.is_project_owner(project_id, user_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only project owners can delete projects"
        )
    
    # Delete the project (this will cascade delete related records)
    ProjectService.delete_project(project_id)
    return {"message": "Project deleted successfully"}

@router.get("/{project_id}/members", response_model=List[ProjectMemberOut])
def get_project_members(project_id: str, user_id: str = Depends(get_current_user_id)):
    # Check if user is a member of the project
    if not ProjectService.is_project_member(project_id, user_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied: You are not a member of this project"
        )
    return ProjectService.get_project_members(project_id)

@router.post("/{project_id}/add_member", response_model=ProjectMemberOut, status_code=status.HTTP_201_CREATED)
def add_project_member(project_id: str, payload: ProjectMemberAdd, user_id: str = Depends(get_current_user_id)):
    # Check if user is owner or manager of the project
    if not ProjectService.can_manage_project(project_id, user_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only project owners and managers can add members"
        )
    
    # Check if target user exists
    target_user = UserService.get_user_by_email(payload.email)
    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Always assign "staff" role for new members
    return ProjectService.add_project_member(project_id, target_user["id"], "staff")

@router.patch("/{project_id}/members/{member_id}/role")
def update_project_member_role(project_id: str, member_id: str, new_role: str, user_id: str = Depends(get_current_user_id)):
    # Check if user is owner or manager of the project
    if not ProjectService.can_manage_project(project_id, user_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only project owners and managers can update member roles"
        )
    
    # Update the member's role
    ProjectService.update_project_member_role(project_id, member_id, new_role)
    return {"message": "Member role updated successfully"}

@router.delete("/{project_id}/members/{member_id}")
def remove_project_member(project_id: str, member_id: str, user_id: str = Depends(get_current_user_id)):
    # Check if user is owner or manager of the project
    if not ProjectService.can_manage_project(project_id, user_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only project owners and managers can remove members"
        )
    
    # Prevent removing the project owner
    if ProjectService.is_project_owner(project_id, member_id):
        raise HTTPException(
            status_code=400,
            detail="Cannot remove project owner"
        )
    
    ProjectService.remove_project_member(project_id, member_id)
    return {"message": "Member removed successfully"}

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
