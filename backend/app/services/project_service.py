from typing import List, Optional, Dict, Any
from uuid import UUID
from app.services.supabase_service import SupabaseService

class ProjectService:
    @staticmethod
    def create_project(name: str, owner_id: str, cover_url: Optional[str] = None) -> Dict[str, Any]:
        project = {
            "name": name.strip(),
            "owner_id": owner_id,
            "cover_url": cover_url
        }
        result = SupabaseService.insert("projects", project)
        # owner automatically becomes project member (owner)
        SupabaseService.insert("project_members", {
            "project_id": result["id"],
            "user_id": owner_id,
            "role": "owner"
        })
        return result

    @staticmethod
    def list_for_user(user_id: str) -> List[Dict[str, Any]]:
        # find projects where user is member (owner or collaborator/manager/viewer)
        memberships = SupabaseService.select(
            "project_members", filters={"user_id": user_id}
        )
        project_ids = [m["project_id"] for m in memberships]
        if not project_ids:
            return []
        
        # Get projects
        client = SupabaseService.get_client()
        rows = client.table("projects").select("*").in_("id", project_ids).order("created_at", desc=True).execute()
        projects = rows.data or []
        
        # Get unique owner IDs
        owner_ids = list(set([project["owner_id"] for project in projects]))
        
        # Fetch owner information from users table
        owner_info = {}
        if owner_ids:
            owner_rows = client.table("users").select("id, display_name, email").in_("id", owner_ids).execute()
            for owner in owner_rows.data or []:
                owner_info[owner["id"]] = {
                    "display_name": owner.get("display_name"),
                    "email": owner.get("email")
                }
        
        # Add user's role and owner display name to each project
        for project in projects:
            user_membership = next((m for m in memberships if m["project_id"] == project["id"]), None)
            project["user_role"] = user_membership["role"] if user_membership else "member"
            
            # Add owner display name
            owner_data = owner_info.get(project["owner_id"], {})
            project["owner_display_name"] = owner_data.get("display_name") or owner_data.get("email", "Unknown")
        
        return projects

    @staticmethod
    def add_task(project_id: str, title: str, assignee_id: Optional[str] = None) -> Dict[str, Any]:
        payload = {"project_id": project_id, "title": title.strip()}
        if assignee_id:
            payload["assignee_id"] = assignee_id
        return SupabaseService.insert("tasks", payload)

    @staticmethod
    def reassign_task(task_id: str, new_project_id: Optional[str]) -> Dict[str, Any]:
        return SupabaseService.update("tasks", {"project_id": new_project_id}, {"id": task_id})

    @staticmethod
    def tasks_by_project(project_id: str) -> List[Dict[str, Any]]:
        return SupabaseService.select("tasks", filters={"project_id": project_id})

    @staticmethod
    def tasks_grouped_kanban(project_id: str) -> Dict[str, List[Dict[str, Any]]]:
        rows = ProjectService.tasks_by_project(project_id)
        kanban = {"todo": [], "in_progress": [], "review": [], "done": []}
        for r in rows:
            kanban.setdefault(r["status"], []).append(r)
        return kanban

    @staticmethod
    def is_project_member(project_id: str, user_id: str) -> bool:
        """Check if user is a member of the project"""
        memberships = SupabaseService.select(
            "project_members", 
            filters={"project_id": project_id, "user_id": user_id}
        )
        return len(memberships) > 0

    @staticmethod
    def is_project_owner(project_id: str, user_id: str) -> bool:
        """Check if user is the owner of the project"""
        memberships = SupabaseService.select(
            "project_members", 
            filters={"project_id": project_id, "user_id": user_id, "role": "owner"}
        )
        return len(memberships) > 0

    @staticmethod
    def can_manage_project(project_id: str, user_id: str) -> bool:
        """Check if user can manage the project (owner or manager)"""
        memberships = SupabaseService.select(
            "project_members", 
            filters={"project_id": project_id, "user_id": user_id}
        )
        if not memberships:
            return False
        
        user_role = memberships[0]["role"]
        return user_role in ["owner", "manager"]

    @staticmethod
    def get_project_members(project_id: str) -> List[Dict[str, Any]]:
        """Get all members of a project with user details"""
        client = SupabaseService.get_client()
        result = client.table("project_members").select(
            "project_id, user_id, role, users(email, display_name)"
        ).eq("project_id", project_id).execute()
        
        members = []
        for row in result.data or []:
            user_data = row.get("users", {})
            members.append({
                "project_id": row["project_id"],
                "user_id": row["user_id"],
                "role": row["role"],
                "user_email": user_data.get("email"),
                "user_display_name": user_data.get("display_name")
            })
        
        return members

    @staticmethod
    def add_project_member(project_id: str, user_id: str, role: str) -> Dict[str, Any]:
        """Add a user to a project"""
        # Check if user is already a member
        existing = SupabaseService.select(
            "project_members",
            filters={"project_id": project_id, "user_id": user_id}
        )
        if existing:
            raise ValueError("User is already a member of this project")
        
        member_data = {
            "project_id": project_id,
            "user_id": user_id,
            "role": role
        }
        return SupabaseService.insert("project_members", member_data)

    @staticmethod
    def update_project_member_role(project_id: str, user_id: str, new_role: str) -> Dict[str, Any]:
        """Update a project member's role"""
        result = SupabaseService.update(
            "project_members",
            {"role": new_role},
            {"project_id": project_id, "user_id": user_id}
        )
        return result

    @staticmethod
    def remove_project_member(project_id: str, user_id: str) -> bool:
        """Remove a user from a project"""
        result = SupabaseService.delete(
            "project_members",
            filters={"project_id": project_id, "user_id": user_id}
        )
        return result

    @staticmethod
    def delete_project(project_id: str) -> bool:
        """Delete a project and all its related data"""
        # Delete project members first (if not cascade)
        SupabaseService.delete("project_members", filters={"project_id": project_id})
        
        # Delete project tasks (if not cascade)
        SupabaseService.delete("tasks", filters={"project_id": project_id})
        
        # Delete the project itself
        result = SupabaseService.delete("projects", filters={"id": project_id})
        return result