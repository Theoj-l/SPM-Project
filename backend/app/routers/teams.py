from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..models.team import TeamCreate, TeamUpdate, TeamOut, TeamMemberOut, TeamMemberAdd
from ..services.team_service import TeamService
from ..routers.projects import get_current_user_id

router = APIRouter(tags=["teams"])

@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(payload: TeamCreate, user_id: str = Depends(get_current_user_id)):
    """Create a new team"""
    try:
        return TeamService.create_team(payload, user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[TeamOut])
def list_my_teams(user_id: str = Depends(get_current_user_id)):
    """List teams that the current user is a member of"""
    return TeamService.list_teams_for_user(user_id)

@router.get("/admin/all", response_model=List[TeamOut])
def list_all_teams_admin(user_id: str = Depends(get_current_user_id)):
    """List all teams in the system (admin only)"""
    try:
        return TeamService.list_all_teams(user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: str, user_id: str = Depends(get_current_user_id)):
    """Get team by ID"""
    team = TeamService.get_team_by_id(team_id, user_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.put("/{team_id}", response_model=TeamOut)
def update_team(team_id: str, payload: TeamUpdate, user_id: str = Depends(get_current_user_id)):
    """Update team"""
    try:
        team = TeamService.update_team(team_id, payload, user_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        return team
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.delete("/{team_id}")
def delete_team(team_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete team"""
    try:
        success = TeamService.delete_team(team_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Team not found")
        return {"message": "Team deleted successfully"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.post("/{team_id}/members")
def add_team_member(team_id: str, payload: TeamMemberAdd, user_id: str = Depends(get_current_user_id)):
    """Add member to team"""
    try:
        success = TeamService.add_team_member(team_id, user_id, payload.member_user_id, payload.role)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add member")
        return {"message": "Member added successfully"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{team_id}/members/{member_user_id}")
def remove_team_member(team_id: str, member_user_id: str, user_id: str = Depends(get_current_user_id)):
    """Remove member from team"""
    try:
        success = TeamService.remove_team_member(team_id, user_id, member_user_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to remove member")
        return {"message": "Member removed successfully"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/{team_id}/members", response_model=List[TeamMemberOut])
def get_team_members(team_id: str, user_id: str = Depends(get_current_user_id)):
    """Get team members"""
    members = TeamService.get_team_members(team_id, user_id)
    return members
