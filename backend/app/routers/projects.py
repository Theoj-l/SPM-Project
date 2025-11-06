print("✅ Loaded projects.py router file")

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import List, Dict, Optional
from app.models.project import ProjectCreate, ProjectOut, ProjectMemberAdd, ProjectMemberOut, TaskOut, TaskCreate, TaskReassign, TaskAssigneeUpdate
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
    
    # Check if user can create projects (managers or admin+manager/staff)
    user_roles = ProjectService.get_user_roles(user_id)
    can_create = False
    
    if "admin" in user_roles:
        # Admin alone is read-only, need manager or staff for management
        if "manager" in user_roles or "staff" in user_roles:
            can_create = True
    else:
        # Check if user is manager
        can_create = "manager" in user_roles
    
    if not can_create:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Manager role or Admin+Manager/Staff required to create projects"
        )
    
    return ProjectService.create_project(name=payload.name, owner_id=user_id, cover_url=payload.cover_url)

@router.get("", response_model=List[ProjectOut])
def list_my_projects(user_id: str = Depends(get_current_user_id), include_archived: bool = False):
    return ProjectService.list_for_user(user_id, include_archived)

@router.get("/admin/all", response_model=List[ProjectOut])
def list_all_projects_admin(user_id: str = Depends(get_current_user_id), include_archived: bool = False):
    """List all projects in the system (admin only)"""
    # Check if user is admin
    user_roles = ProjectService.get_user_roles(user_id)
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Admin role required"
        )
    return ProjectService.list_all_projects(include_archived)

@router.get("/archived", response_model=List[ProjectOut])
def list_archived_projects(user_id: str = Depends(get_current_user_id)):
    """List archived projects for the current user"""
    return ProjectService.list_for_user(user_id, include_archived=True)

@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a specific project by ID"""
    project = ProjectService.get_project_by_id(project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

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

@router.post("/{project_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def add_task(project_id: str, payload: TaskCreate, user_id: str = Depends(get_current_user_id)):
    # Check if user is a member of the project
    if not ProjectService.is_project_member(project_id, user_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied: You are not a member of this project"
        )
    
    # Validate project is active
    project = ProjectService.get_project_by_id(project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.get("status") != "active":
        raise HTTPException(
            status_code=400,
            detail="Tasks can only be created in active projects"
        )
    
    # Creator is default assignee - add if not already in list
    assignee_ids = list(payload.assignee_ids) if payload.assignee_ids else []
    if user_id not in assignee_ids:
        assignee_ids.insert(0, user_id)  # Add creator as first assignee
    
    # Ensure max 5 assignees total
    if len(assignee_ids) > 5:
        assignee_ids = assignee_ids[:5]
    
    return ProjectService.add_task(
        project_id=project_id, 
        title=payload.title, 
        description=payload.description,
        due_date=payload.due_date,
        notes=payload.notes,
        assignee_ids=assignee_ids,
        status=payload.status,
        tags=payload.tags,  # Already parsed as list by validator
        recurring=payload.recurring,
        priority=payload.priority
    )

@router.get("/{project_id}/tasks", response_model=List[TaskOut])
def get_project_tasks(project_id: str, user_id: str = Depends(get_current_user_id), include_archived: bool = False):
    # Check if user is a member of the project
    if not ProjectService.is_project_member(project_id, user_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied: You are not a member of this project"
        )
    # Apply department-based filtering
    return ProjectService.tasks_by_project(project_id, include_archived, user_id)

@router.patch("/tasks/{task_id}/reassign", response_model=TaskOut)
def reassign_task(task_id: str, payload: TaskReassign, user_id: str = Depends(get_current_user_id)):
    return ProjectService.reassign_task(task_id, payload.new_project_id)

@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: str, updates: dict, user_id: str = Depends(get_current_user_id)):
    # Get the task to check project membership
    task = ProjectService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if user is a member of the project
    if not ProjectService.is_project_member(task["project_id"], user_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied: You are not a member of this project"
        )
    
    return ProjectService.update_task(task_id, updates)

@router.delete("/tasks/{task_id}")
def delete_task(task_id: str, user_id: str = Depends(get_current_user_id)):
    # Get the task to check project membership
    task = ProjectService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if user is a member of the project
    if not ProjectService.is_project_member(task["project_id"], user_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied: You are not a member of this project"
        )
    
    ProjectService.delete_task(task_id)
    return {"message": "Task deleted successfully"}

@router.patch("/tasks/{task_id}/assignees", response_model=TaskOut)
def update_task_assignees(task_id: str, payload: TaskAssigneeUpdate, user_id: str = Depends(get_current_user_id)):
    # Get the task to check project membership
    task = ProjectService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if user is a member of the project
    if not ProjectService.is_project_member(task["project_id"], user_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied: You are not a member of this project"
        )
    
    try:
        updated_task = ProjectService.update_task_assignees(task_id, payload.assignee_ids, user_id)
        return ProjectService.get_task(task_id)  # Return full task with assignee names
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}/kanban")
def kanban(project_id: str, user_id: str = Depends(get_current_user_id)) -> Dict[str, list]:
    return ProjectService.tasks_grouped_kanban(project_id, user_id)

@router.get("/tasks/by-tag/{tag}", response_model=List[TaskOut])
def get_tasks_by_tag(tag: str, user_id: str = Depends(get_current_user_id), include_archived: bool = False):
    """Get all tasks with a specific tag, filtered by department access control"""
    return ProjectService.tasks_by_tag(tag, user_id, include_archived)

@router.get("/archived", response_model=List[ProjectOut])
def list_archived_projects(user_id: str = Depends(get_current_user_id)):
    """List archived projects for the current user"""
    projects = ProjectService.list_archived_for_user(user_id)
    return projects

@router.patch("/{project_id}/archive")
def archive_project(project_id: str, user_id: str = Depends(get_current_user_id)):
    """Archive a project (owner only)"""
    try:
        ProjectService.archive_project(project_id, user_id)
        return {"message": "Project archived successfully"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.patch("/{project_id}/restore")
def restore_project(project_id: str, user_id: str = Depends(get_current_user_id)):
    """Restore an archived project (owner only)"""
    try:
        ProjectService.restore_project(project_id, user_id)
        return {"message": "Project restored successfully"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/user/{target_user_id}", response_model=List[ProjectOut])
def get_user_projects(target_user_id: str, user_id: str = Depends(get_current_user_id), include_archived: bool = False):
    """Get projects for a specific user (admins, managers, or team managers can view)"""
    # Check if current user has permission to view other user's projects
    user_roles = ProjectService.get_user_roles(user_id)
    
    # Admins can view anyone's projects
    if "admin" in user_roles:
        return ProjectService.list_for_user(target_user_id, include_archived)
    
    # Managers can view anyone's projects
    if "manager" in user_roles:
        return ProjectService.list_for_user(target_user_id, include_archived)
    
    # Users can only view their own projects
    if target_user_id == user_id:
        return ProjectService.list_for_user(target_user_id, include_archived)
    
    # Check if users are in the same team
    from app.services.team_service import TeamService
    user_teams = TeamService.list_teams_for_user(user_id)
    target_user_teams = TeamService.list_teams_for_user(target_user_id)
    
    # If they share a team, allow viewing (for team collaboration)
    user_team_ids = {team["id"] for team in user_teams}
    target_team_ids = {team["id"] for team in target_user_teams}
    
    if user_team_ids & target_team_ids:  # If there's any overlap
        return ProjectService.list_for_user(target_user_id, include_archived)
    
    raise HTTPException(
        status_code=403,
        detail="Access denied: You don't have permission to view this user's projects"
    )
