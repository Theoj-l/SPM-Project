from typing import List, Optional, Dict, Any
from uuid import UUID
from app.services.supabase_service import SupabaseService
from app.supabase_client import get_supabase_client

class ProjectService:
    @staticmethod
    def get_user_roles(user_id: str) -> List[str]:
        """Get user roles from the users table"""
        try:
            user = SupabaseService.select("users", filters={"id": user_id})
            if user and len(user) > 0:
                return user[0].get("roles", [])
            return []
        except Exception as e:
            print(f"Error getting user roles: {e}")
            return []
    
    @staticmethod
    def create_project(name: str, owner_id: str, cover_url: Optional[str] = None) -> Dict[str, Any]:
        project = {
            "name": name.strip(),
            "owner_id": owner_id,
            "cover_url": cover_url,
            "status": "active"
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
    def list_for_user(user_id: str, include_archived: bool = False) -> List[Dict[str, Any]]:
        # find projects where user is member (owner or collaborator/manager/viewer)
        memberships = SupabaseService.select(
            "project_members", filters={"user_id": user_id}
        )
        project_ids = [m["project_id"] for m in memberships]
        if not project_ids:
            return []
        
        # Get projects (active ones and those without status set)
        client = SupabaseService.get_client()
        rows = client.table("projects").select("*").in_("id", project_ids).order("created_at", desc=True).execute()
        projects = rows.data or []
        
        # Filter projects based on include_archived parameter
        if include_archived:
            # Include both active and archived projects
            projects = [p for p in projects if not p.get("status") or p.get("status") in ["active", "archived"]]
        else:
            # Only include active projects (default behavior)
            projects = [p for p in projects if not p.get("status") or p.get("status") == "active"]
        
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
    def get_project_by_id(project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific project by ID if user has access to it"""
        # Check if user is a member of the project
        memberships = SupabaseService.select(
            "project_members", filters={"user_id": user_id, "project_id": project_id}
        )
        if not memberships:
            return None
        
        # Get the project
        client = SupabaseService.get_client()
        rows = client.table("projects").select("*").eq("id", project_id).execute()
        projects = rows.data or []
        
        if not projects:
            return None
        
        project = projects[0]
        
        # Get owner information
        owner_rows = client.table("users").select("id, display_name, email").eq("id", project["owner_id"]).execute()
        owner_data = owner_rows.data[0] if owner_rows.data else {}
        
        # Add user's role and owner display name
        user_membership = memberships[0]
        project["user_role"] = user_membership["role"]
        project["owner_display_name"] = owner_data.get("display_name") or owner_data.get("email", "Unknown")
        
        return project

    @staticmethod
    def add_task(project_id: str, title: str, description: Optional[str] = None, 
                 due_date: Optional[str] = None, notes: Optional[str] = None,
                 assignee_ids: Optional[List[str]] = None, status: str = "todo") -> Dict[str, Any]:
        payload = {
            "project_id": project_id, 
            "title": title.strip(),
            "status": status
        }
        
        if description:
            payload["description"] = description.strip()
        if due_date:
            payload["due_date"] = due_date
        if notes:
            payload["notes"] = notes.strip()
        if assignee_ids:
            payload["assigned"] = assignee_ids  # Using 'assigned' field from database schema
            
        return SupabaseService.insert("tasks", payload)

    @staticmethod
    def reassign_task(task_id: str, new_project_id: Optional[str]) -> Dict[str, Any]:
        return SupabaseService.update("tasks", {"project_id": new_project_id}, {"id": task_id})

    @staticmethod
    def tasks_by_project(project_id: str, include_archived: bool = False) -> List[Dict[str, Any]]:
        filters = {"project_id": project_id}
        if not include_archived:
            filters["type"] = "active"
        tasks = SupabaseService.select("tasks", filters=filters)
        
        # Get all unique assignee IDs from all tasks
        assignee_ids = set()
        for task in tasks:
            if task.get("assigned"):
                assignee_ids.update(task["assigned"])
        
        # Fetch assignee information
        assignee_info = {}
        if assignee_ids:
            client = get_supabase_client()
            assignee_rows = client.table("users").select("id, display_name, email").in_("id", list(assignee_ids)).execute()
            for assignee in assignee_rows.data or []:
                assignee_info[assignee["id"]] = {
                    "display_name": assignee.get("display_name"),
                    "email": assignee.get("email")
                }
        
        # Add assignee names to each task
        for task in tasks:
            task["assignee_ids"] = task.get("assigned", [])
            task["assignee_names"] = []
            if task.get("assigned"):
                for assignee_id in task["assigned"]:
                    assignee_data = assignee_info.get(assignee_id, {})
                    name = assignee_data.get("display_name") or assignee_data.get("email", "Unknown")
                    task["assignee_names"].append(name)
        
        return tasks

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

    @staticmethod
    def list_archived_for_user(user_id: str) -> List[Dict[str, Any]]:
        """List archived projects for a user"""
        # find projects where user is member (owner or collaborator/manager/viewer)
        memberships = SupabaseService.select(
            "project_members", filters={"user_id": user_id}
        )
        project_ids = [m["project_id"] for m in memberships]
        if not project_ids:
            return []
        
        # Get archived projects
        client = SupabaseService.get_client()
        rows = client.table("projects").select("*").in_("id", project_ids).eq("status", "archived").order("created_at", desc=True).execute()
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
        
        # Attach user role and owner display name to each project
        for project in projects:
            user_membership = next((m for m in memberships if m["project_id"] == project["id"]), None)
            project["user_role"] = user_membership["role"] if user_membership else "member"
            
            owner_data = owner_info.get(project["owner_id"], {})
            project["owner_display_name"] = owner_data.get("display_name") or owner_data.get("email", "Unknown")
            
            # Ensure status is set (default to "active" if null)
            if not project.get("status"):
                project["status"] = "active"
        
        return projects

    @staticmethod
    def archive_project(project_id: str, user_id: str) -> Dict[str, Any]:
        """Archive a project (owner only)"""
        # Check if user is owner
        if not ProjectService.is_project_owner(project_id, user_id):
            raise PermissionError("Only project owners can archive projects")
        
        # Update project status to archived
        result = SupabaseService.update(
            "projects",
            {"status": "archived"},
            {"id": project_id}
        )
        return result

    @staticmethod
    def restore_project(project_id: str, user_id: str) -> Dict[str, Any]:
        """Restore an archived project (owner only)"""
        # Check if user is owner
        if not ProjectService.is_project_owner(project_id, user_id):
            raise PermissionError("Only project owners can restore projects")
        
        # Update project status to active
        result = SupabaseService.update(
            "projects",
            {"status": "active"},
            {"id": project_id}
        )
        return result

    @staticmethod
    def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        """Get a single task by ID"""
        result = SupabaseService.select("tasks", filters={"id": task_id})
        return result[0] if result else None

    @staticmethod
    def update_task(task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a task"""
        return SupabaseService.update("tasks", updates, {"id": task_id})

    @staticmethod
    def delete_task(task_id: str) -> Dict[str, Any]:
        """Delete a task"""
        return SupabaseService.delete("tasks", {"id": task_id})

    @staticmethod
    def update_task_assignees(task_id: str, assignee_ids: List[str]) -> Dict[str, Any]:
        """Update task assignees"""
        return SupabaseService.update("tasks", {"assigned": assignee_ids}, {"id": task_id})