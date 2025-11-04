from typing import List, Optional, Dict, Any
from ..models.team import TeamCreate, TeamUpdate, TeamOut, TeamMemberOut
from .supabase_service import SupabaseService
from .project_service import ProjectService

class TeamService:
    @staticmethod
    def create_team(team_data: TeamCreate, manager_id: str) -> TeamOut:
        """Create a new team with the creator as manager"""
        # Only managers can create teams
        user_roles = ProjectService.get_user_roles(manager_id)
        
        if "manager" not in user_roles:
            raise PermissionError("Access denied: Only managers can create teams")
        
        # Create team
        team_result = SupabaseService.insert(
            "teams",
            {
                "name": team_data.name,
                "description": team_data.description,
                "manager_id": manager_id
            }
        )
        
        if not team_result:
            raise Exception("Failed to create team")
        
        team = team_result
        
        # Add creator as team manager
        SupabaseService.insert(
            "team_members",
            {
                "team_id": team["id"],
                "user_id": manager_id,
                "role": "manager"
            }
        )
        
        return TeamOut(**team)
    
    @staticmethod
    def list_teams_for_user(user_id: str) -> List[TeamOut]:
        """List teams based on user role:
        - Manager: Teams they created and are part of
        - Staff: Teams they are part of
        - Admin: All teams (read-only)
        """
        user_roles = ProjectService.get_user_roles(user_id)
        
        # Admin can see all teams
        if "admin" in user_roles:
            all_teams = SupabaseService.select("teams")
            return [TeamOut(**team) for team in all_teams] if all_teams else []
        
        # Get user's team memberships
        memberships = SupabaseService.select(
            "team_members",
            filters={"user_id": user_id}
        )
        
        if not memberships:
            return []
        
        team_ids = [membership["team_id"] for membership in memberships]
        
        # Get team details
        teams = []
        for team_id in team_ids:
            team_result = SupabaseService.select("teams", filters={"id": team_id})
            if team_result:
                teams.extend(team_result)
        
        return [TeamOut(**team) for team in teams]
    
    @staticmethod
    def list_all_teams(user_id: str) -> List[TeamOut]:
        """List all teams in the system (admin only)"""
        # Check if user is admin
        user_roles = ProjectService.get_user_roles(user_id)
        if "admin" not in user_roles:
            raise PermissionError("Access denied: Admin role required")
        
        teams = SupabaseService.select("teams")
        return [TeamOut(**team) for team in teams]
    
    @staticmethod
    def get_team_by_id(team_id: str, user_id: str) -> Optional[TeamOut]:
        """Get team by ID with access validation"""
        # Check if user is admin (can access any team)
        user_roles = ProjectService.get_user_roles(user_id)
        if "admin" in user_roles:
            team_result = SupabaseService.select("teams", filters={"id": team_id})
            if team_result:
                return TeamOut(**team_result[0])
            return None
        
        # Check if user is member of the team
        membership_result = SupabaseService.select(
            "team_members",
            filters={"team_id": team_id, "user_id": user_id}
        )
        
        if not membership_result:
            return None
        
        team_result = SupabaseService.select("teams", filters={"id": team_id})
        if team_result:
            return TeamOut(**team_result[0])
        
        return None
    
    @staticmethod
    def update_team(team_id: str, updates: TeamUpdate, user_id: str) -> Optional[TeamOut]:
        """Update team with role-based access control:
        - Manager: Can update teams they manage
        - Staff: Cannot update teams (only managers can update)
        - Admin: Read-only, cannot update teams
        - Admin + Manager: Can update teams they manage
        - Admin + Staff: Cannot update teams (only managers can update)
        """
        # Check if user can manage teams
        user_roles = ProjectService.get_user_roles(user_id)
        
        # Admin alone is read-only
        if "admin" in user_roles and "manager" not in user_roles and "staff" not in user_roles:
            raise PermissionError("Access denied: Admin role is read-only")
        
        # Only managers can update teams
        if "manager" not in user_roles:
            raise PermissionError("Access denied: Only managers can update teams")
        
        # Check if user is team manager
        membership_result = SupabaseService.select(
            "team_members",
            filters={"team_id": team_id, "user_id": user_id, "role": "manager"}
        )
        is_team_manager = len(membership_result) > 0
        
        if not is_team_manager:
            raise PermissionError("Access denied: Only team managers can update teams")
        
        # Prepare update data
        update_data = {}
        if updates.name is not None:
            update_data["name"] = updates.name
        if updates.description is not None:
            update_data["description"] = updates.description
        
        if not update_data:
            return TeamService.get_team_by_id(team_id, user_id)
        
        # Update team
        result = SupabaseService.update(
            "teams",
            update_data,
            {"id": team_id}
        )
        
        if result:
            return TeamService.get_team_by_id(team_id, user_id)
        
        return None
    
    @staticmethod
    def delete_team(team_id: str, user_id: str) -> bool:
        """Delete team with role-based access control:
        - Manager: Can delete teams they manage
        - Staff: Cannot delete teams (only managers can delete)
        - Admin: Read-only, cannot delete teams
        - Admin + Manager: Can delete teams they manage
        - Admin + Staff: Cannot delete teams (only managers can delete)
        """
        # Check if user can manage teams
        user_roles = ProjectService.get_user_roles(user_id)
        
        # Admin alone is read-only
        if "admin" in user_roles and "manager" not in user_roles and "staff" not in user_roles:
            raise PermissionError("Access denied: Admin role is read-only")
        
        # Only managers can delete teams
        if "manager" not in user_roles:
            raise PermissionError("Access denied: Only managers can delete teams")
        
        # Check if user is team manager
        membership_result = SupabaseService.select(
            "team_members",
            filters={"team_id": team_id, "user_id": user_id, "role": "manager"}
        )
        is_team_manager = len(membership_result) > 0
        
        if not is_team_manager:
            raise PermissionError("Access denied: Only team managers can delete teams")
        
        # Delete team (cascade will handle team_members)
        result = SupabaseService.delete("teams", {"id": team_id})
        return result
    
    @staticmethod
    def add_team_member(team_id: str, user_id: str, member_user_id: str, role: str = "member") -> bool:
        """Add member to team with role-based access control:
        - Manager: Can add members to teams they manage
        - Staff: Can add members to teams they're members of
        - Admin: Read-only, cannot add members
        - Admin + Manager: Can add members to teams they manage
        - Admin + Staff: Can add members to teams they're members of
        """
        # Check if user can manage team
        user_roles = ProjectService.get_user_roles(user_id)
        member_roles = ProjectService.get_user_roles(member_user_id)
        
        # Admin alone is read-only
        if "admin" in user_roles and "manager" not in user_roles and "staff" not in user_roles:
            raise PermissionError("Access denied: Admin role is read-only")
        
        # Check if user is team manager
        membership_result = SupabaseService.select(
            "team_members",
            filters={"team_id": team_id, "user_id": user_id, "role": "manager"}
        )
        is_team_manager = len(membership_result) > 0
        
        # Check if user is team member (for staff adding other staff)
        member_membership_result = SupabaseService.select(
            "team_members",
            filters={"team_id": team_id, "user_id": user_id}
        )
        is_team_member = len(member_membership_result) > 0
        
        # Determine if user can add this member
        can_add = False
        
        if "manager" in user_roles and is_team_manager:
            # Manager can add staff, users, and admins to teams they manage
            can_add = True
        elif "staff" in user_roles and is_team_member:
            # Staff can only add other staff (not managers or admins) to teams they're members of
            can_add = "staff" in member_roles and "manager" not in member_roles and "admin" not in member_roles
        
        if not can_add:
            if "staff" in user_roles:
                raise PermissionError("Access denied: Staff can only add other staff members")
            else:
                raise PermissionError("Access denied: Only team managers can add members")
        
        # Check if member is already in the team
        existing_member = SupabaseService.select(
            "team_members",
            filters={"team_id": team_id, "user_id": member_user_id}
        )
        if existing_member:
            raise ValueError("User is already a member of this team")
        
        # Add member
        result = SupabaseService.insert(
            "team_members",
            {
                "team_id": team_id,
                "user_id": member_user_id,
                "role": role
            }
        )
        
        return result is not None
    
    @staticmethod
    def remove_team_member(team_id: str, user_id: str, member_user_id: str) -> bool:
        """Remove member from team with role-based access control:
        - Manager: Can remove members from teams they manage
        - Staff: Can remove members from teams they're members of
        - Admin: Read-only, cannot remove members
        - Admin + Manager: Can remove members from teams they manage
        - Admin + Staff: Can remove members from teams they're members of
        """
        # Check if user can manage team
        user_roles = ProjectService.get_user_roles(user_id)
        
        # Admin alone is read-only
        if "admin" in user_roles and "manager" not in user_roles and "staff" not in user_roles:
            raise PermissionError("Access denied: Admin role is read-only")
        
        # Check if user is team manager
        membership_result = SupabaseService.select(
            "team_members",
            filters={"team_id": team_id, "user_id": user_id, "role": "manager"}
        )
        is_team_manager = len(membership_result) > 0
        
        # Check if user is team member (for staff removing members)
        member_membership_result = SupabaseService.select(
            "team_members",
            filters={"team_id": team_id, "user_id": user_id}
        )
        is_team_member = len(member_membership_result) > 0
        
        # Determine if user can remove members
        can_remove = False
        
        if "manager" in user_roles and is_team_manager:
            # Manager can remove members from teams they manage
            can_remove = True
        elif "staff" in user_roles and is_team_member:
            # Staff can remove members from teams they're members of
            can_remove = True
        
        if not can_remove:
            raise PermissionError("Access denied: Only team managers or team members can remove members")
        
        # Prevent team manager from removing themselves
        target_member = SupabaseService.select(
            "team_members",
            filters={"team_id": team_id, "user_id": member_user_id}
        )
        if target_member and len(target_member) > 0:
            target_role = target_member[0].get("role")
            if target_role == "manager" and member_user_id == user_id:
                raise ValueError("Team managers cannot remove themselves from the team")
        
        # Remove member
        result = SupabaseService.delete(
            "team_members",
            {"team_id": team_id, "user_id": member_user_id}
        )
        
        return result
    
    @staticmethod
    def get_team_members(team_id: str, user_id: str) -> List[TeamMemberOut]:
        """Get team members with access validation"""
        # Check if user has access to team
        team = TeamService.get_team_by_id(team_id, user_id)
        if not team:
            return []
        
        members = SupabaseService.select(
            "team_members",
            filters={"team_id": team_id}
        )
        
        return [TeamMemberOut(**member) for member in members]
