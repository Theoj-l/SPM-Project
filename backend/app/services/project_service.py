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
        # supabase python: .in_("id", project_ids)
        client = SupabaseService.get_client()
        rows = client.table("projects").select("*").in_("id", project_ids).order("created_at", desc=True).execute()
        return rows.data or []

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
