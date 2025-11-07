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
    def can_admin_manage(user_id: str) -> bool:
        """Check if admin user can manage projects (has manager or staff role)"""
        user_roles = ProjectService.get_user_roles(user_id)
        return "admin" in user_roles and ("manager" in user_roles or "staff" in user_roles)
    
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
        try:
            # find projects where user is member (owner or collaborator/manager/viewer)
            memberships = SupabaseService.select(
                "project_members", filters={"user_id": user_id}
            )
            if not memberships:
                return []
            
            project_ids = [m["project_id"] for m in memberships]
            if not project_ids:
                return []
            
            # Get projects (active ones and those without status set)
            client = SupabaseService.get_client()
            rows = client.table("projects").select("*").in_("id", project_ids).order("created_at", desc=True).execute()
            projects = rows.data or []
        except Exception as e:
            print(f"Error fetching projects for user {user_id}: {e}")
            # Return empty list on error to prevent blocking the login
            return []
        
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
            try:
                owner_rows = client.table("users").select("id, display_name, email").in_("id", owner_ids).execute()
                for owner in owner_rows.data or []:
                    owner_info[owner["id"]] = {
                        "display_name": owner.get("display_name"),
                        "email": owner.get("email")
                    }
            except Exception as e:
                print(f"Error fetching owner information: {e}")
                # Continue without owner info if query fails
        
        # Add user's role and owner display name to each project
        for project in projects:
            user_membership = next((m for m in memberships if m["project_id"] == project["id"]), None)
            project["user_role"] = user_membership["role"] if user_membership else "member"
            
            # Add owner display name
            owner_data = owner_info.get(project["owner_id"], {})
            project["owner_display_name"] = owner_data.get("display_name") or owner_data.get("email", "Unknown")
        
        return projects

    @staticmethod
    def list_all_projects(include_archived: bool = False) -> List[Dict[str, Any]]:
        """List all projects in the system (admin only)"""
        client = SupabaseService.get_client()
        
        # Get all projects
        rows = client.table("projects").select("*").order("created_at", desc=True).execute()
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
        
        # Add owner display name to each project
        for project in projects:
            owner_data = owner_info.get(project["owner_id"], {})
            project["owner_display_name"] = owner_data.get("display_name") or owner_data.get("email", "Unknown")
            # For admin view, we don't need user_role since admin can see all projects
        
        return projects

    @staticmethod
    def get_project_by_id(project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific project by ID if user has access to it"""
        # Check if user is admin first
        user_roles = ProjectService.get_user_roles(user_id)
        is_admin = "admin" in user_roles
        
        # Check if user is a member of the project (unless admin)
        memberships = []
        if not is_admin:
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
        if is_admin:
            project["user_role"] = "admin"
        else:
            user_membership = memberships[0]
            project["user_role"] = user_membership["role"]
        project["owner_display_name"] = owner_data.get("display_name") or owner_data.get("email", "Unknown")
        
        return project

    @staticmethod
    def add_task(project_id: str, title: str, description: Optional[str] = None, 
                 due_date: Optional[str] = None, notes: Optional[str] = None,
                 assignee_ids: Optional[List[str]] = None, status: str = "todo",
                 tags: Optional[List[str]] = None, recurring: Optional[dict] = None,
                 priority: Optional[int] = None) -> Dict[str, Any]:
        """Create a task. If recurring is enabled, expand into multiple individual tasks up to end_date.
        Returns the first created task for API compatibility."""

        def base_payload(due_date_value: Optional[str]) -> Dict[str, Any]:
            payload: Dict[str, Any] = {
                "project_id": project_id,
                "title": title.strip(),
                "status": status,
            }
            if description:
                payload["description"] = description.strip()
            if due_date_value:
                payload["due_date"] = due_date_value
            if notes:
                payload["notes"] = notes.strip()
            if assignee_ids:
                payload["assigned"] = assignee_ids
            if tags:
                payload["tags"] = tags
            if priority is not None:
                payload["priority"] = priority
            return payload

        # Non-recurring: create single task
        if not recurring or not recurring.get("enabled"):
            task_result = SupabaseService.insert("tasks", base_payload(due_date))
            ProjectService._notify_assignees(project_id, title, assignee_ids, task_result)
            return task_result

        # Recurring: expand into occurrences based on frequency/interval until end_date (inclusive)
        if not due_date:
            raise ValueError("Due date is required for recurring tasks")
        end_date = recurring.get("end_date")
        if not end_date:
            raise ValueError("End date is required for recurring tasks")

        import datetime as _dt

        start = _dt.datetime.strptime(due_date, "%Y-%m-%d").date()
        end = _dt.datetime.strptime(end_date, "%Y-%m-%d").date()
        if end < start:
            raise ValueError("Recurring end date cannot be before start due date")

        frequency = (recurring.get("frequency") or "weekly").lower()
        interval = int(recurring.get("interval") or 1)
        if interval < 1:
            interval = 1

        def add_months(d: _dt.date, months: int) -> _dt.date:
            month = d.month - 1 + months
            year = d.year + month // 12
            month = month % 12 + 1
            day = min(d.day, [31,
                              29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                              31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
            return _dt.date(year, month, day)

        def add_years(d: _dt.date, years: int) -> _dt.date:
            try:
                return d.replace(year=d.year + years)
            except ValueError:
                # Handle Feb 29 -> Feb 28 on non-leap years
                return d.replace(month=2, day=28, year=d.year + years)

        created_results: List[Dict[str, Any]] = []
        current = start
        while current <= end:
            payload = base_payload(current.strftime("%Y-%m-%d"))
            result = SupabaseService.insert("tasks", payload)
            created_results.append(result)

            if frequency == "daily":
                current = current + _dt.timedelta(days=interval)
            elif frequency == "weekly":
                current = current + _dt.timedelta(weeks=interval)
            elif frequency == "monthly":
                current = add_months(current, interval)
            elif frequency == "yearly":
                current = add_years(current, interval)
            else:
                # default to weekly if unknown
                current = current + _dt.timedelta(weeks=interval)

        # Notify assignees for the first created task (avoid spamming)
        first = created_results[0] if created_results else {}
        ProjectService._notify_assignees(project_id, title, assignee_ids, first)
        return first

    @staticmethod
    def _notify_assignees(project_id: str, title: str, assignee_ids: Optional[List[str]], task_result: Optional[Dict[str, Any]]):
        if not (assignee_ids and task_result):
            return
        from app.services.notification_service import NotificationService
        from app.services.email_service import EmailService
        from app.supabase_client import get_supabase_client

        notification_service = NotificationService()
        email_service = EmailService()
        client = get_supabase_client()

        project_result = client.table("projects").select("name").eq("id", project_id).execute()
        project_name = project_result.data[0].get("name", "Unknown Project") if project_result.data else "Unknown Project"

        task_id = task_result.get("id")
        if task_id:
            for assignee_id in assignee_ids:
                notification_service.create_task_assigned_notification(
                    user_id=assignee_id,
                    task_id=task_id,
                    task_title=title,
                    project_id=project_id
                )

                user_result = client.table("users").select("email, display_name").eq("id", assignee_id).execute()
                if user_result.data:
                    user_data = user_result.data[0]
                    email_service.send_task_assigned_email(
                        user_email=user_data.get("email"),
                        user_name=user_data.get("display_name") or user_data.get("email", "").split("@")[0],
                        task_title=title,
                        task_id=task_id,
                        project_name=project_name,
                        project_id=project_id
                    )

    @staticmethod
    def reassign_task(task_id: str, new_project_id: Optional[str]) -> Dict[str, Any]:
        return SupabaseService.update("tasks", {"project_id": new_project_id}, {"id": task_id})

    @staticmethod
    def tasks_by_project(project_id: str, include_archived: bool = False, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tasks for a project, optionally filtered by department access control"""
        filters = {"project_id": project_id}
        if not include_archived:
            filters["type"] = "active"
        tasks = SupabaseService.select("tasks", filters=filters)
        
        # Apply department-based filtering if user_id is provided
        if user_id:
            tasks = ProjectService._filter_tasks_by_department(tasks, user_id)
        
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
    def _filter_tasks_by_department(tasks: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """Filter tasks based on department access control:
        - Staff can see tasks if any assignee is from their department or reporting departments
        - Managers can see all tasks (handled separately)
        """
        client = get_supabase_client()
        
        # Get user's roles and department
        try:
            # First try to get user with department_id
            try:
                user_result = client.table("users").select("id, department_id, roles").eq("id", user_id).execute()
                has_department_column = True
            except Exception:
                # department_id column doesn't exist - fall back to basic query
                user_result = client.table("users").select("id, roles").eq("id", user_id).execute()
                has_department_column = False
            
            if not user_result.data:
                return []  # User not found
            
            user_data = user_result.data[0]
            user_roles = user_data.get("roles", [])
            if isinstance(user_roles, str):
                user_roles = [r.strip().lower() for r in user_roles.split(",")]
            elif isinstance(user_roles, list):
                user_roles = [r.lower() for r in user_roles]
            
            # Managers and admins can see all tasks
            if "manager" in user_roles or "admin" in user_roles:
                return tasks
            
            # If department_id column doesn't exist, use assignment-based filtering
            if not has_department_column:
                # User has no department - can only see tasks they're assigned to
                return [task for task in tasks if task.get("assigned") and user_id in task.get("assigned", [])]
            
            user_department_id = user_data.get("department_id")
            if not user_department_id:
                # User has no department - can only see tasks they're assigned to
                return [task for task in tasks if task.get("assigned") and user_id in task.get("assigned", [])]
        except Exception:
            # If query fails, return all tasks (fallback)
            return tasks
        
        # Get all departments that report to user's department (including user's department)
        accessible_department_ids = {user_department_id}
        try:
            # Get child departments (departments that report to user's department)
            dept_result = client.table("departments").select("id, parent_department_id").execute()
            if dept_result.data:
                # Build a map of parent -> children
                parent_to_children = {}
                for dept in dept_result.data:
                    parent_id = dept.get("parent_department_id")
                    if parent_id:
                        if parent_id not in parent_to_children:
                            parent_to_children[parent_id] = []
                        parent_to_children[parent_id].append(dept["id"])
                
                # Recursively get all child departments
                def get_child_departments(dept_id):
                    children = parent_to_children.get(dept_id, [])
                    result = set(children)
                    for child_id in children:
                        result.update(get_child_departments(child_id))
                    return result
                
                accessible_department_ids.update(get_child_departments(user_department_id))
        except Exception:
            # If departments table doesn't exist or error, just use user's department
            pass
        
        # Get all assignee IDs from tasks
        assignee_ids = set()
        for task in tasks:
            if task.get("assigned"):
                assignee_ids.update(task["assigned"])
        
        # Get departments of all assignees
        assignee_departments = {}
        if assignee_ids:
            try:
                assignees_result = client.table("users").select("id, department_id").in_("id", list(assignee_ids)).execute()
                if assignees_result.data:
                    for assignee in assignees_result.data:
                        assignee_departments[assignee["id"]] = assignee.get("department_id")
            except Exception:
                # If department_id doesn't exist in users table, return all tasks
                return tasks
        
        # Filter tasks: show if any assignee is from accessible departments
        filtered_tasks = []
        for task in tasks:
            assigned = task.get("assigned", [])
            if not assigned:
                continue
            
            # Check if any assignee is from an accessible department
            has_accessible_assignee = False
            for assignee_id in assigned:
                assignee_dept = assignee_departments.get(assignee_id)
                if assignee_dept and assignee_dept in accessible_department_ids:
                    has_accessible_assignee = True
                    break
            
            if has_accessible_assignee:
                filtered_tasks.append(task)
        
        return filtered_tasks

    @staticmethod
    def tasks_grouped_kanban(project_id: str, user_id: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        rows = ProjectService.tasks_by_project(project_id, include_archived=False, user_id=user_id)
        kanban = {"todo": [], "in_progress": [], "review": [], "done": []}
        for r in rows:
            kanban.setdefault(r["status"], []).append(r)
        return kanban
    
    @staticmethod
    def tasks_by_tag(tag: str, user_id: Optional[str] = None, include_archived: bool = False) -> List[Dict[str, Any]]:
        """Get all tasks with a specific tag, filtered by department access control"""
        filters = {}
        if not include_archived:
            filters["type"] = "active"
        
        # Get all tasks
        all_tasks = SupabaseService.select("tasks", filters=filters)
        
        # Filter by tag
        tasks_with_tag = []
        for task in all_tasks:
            task_tags = task.get("tags", [])
            if isinstance(task_tags, list) and tag in task_tags:
                tasks_with_tag.append(task)
        
        # Apply department-based filtering if user_id is provided
        if user_id:
            tasks_with_tag = ProjectService._filter_tasks_by_department(tasks_with_tag, user_id)
        
        # Get all unique assignee IDs from all tasks
        assignee_ids = set()
        for task in tasks_with_tag:
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
        for task in tasks_with_tag:
            task["assignee_ids"] = task.get("assigned", [])
            task["assignee_names"] = []
            if task.get("assigned"):
                for assignee_id in task["assigned"]:
                    assignee_data = assignee_info.get(assignee_id, {})
                    name = assignee_data.get("display_name") or assignee_data.get("email", "Unknown")
                    task["assignee_names"].append(name)
        
        return tasks_with_tag

    @staticmethod
    def is_project_member(project_id: str, user_id: str) -> bool:
        """Check if user is a member of the project or admin"""
        # Check if user is admin first
        user_roles = ProjectService.get_user_roles(user_id)
        if "admin" in user_roles:
            return True
            
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
        """Check if user can manage the project (owner, manager, or admin+manager/staff)"""
        user_roles = ProjectService.get_user_roles(user_id)
        
        # Check if user is admin with additional roles (manager or staff)
        if "admin" in user_roles:
            # Admin alone is read-only, need manager or staff for management
            if "manager" in user_roles or "staff" in user_roles:
                return True
            return False
            
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
        """Archive a project (owner or admin+manager/staff)"""
        user_roles = ProjectService.get_user_roles(user_id)
        
        # Check if user is admin with additional roles
        if "admin" in user_roles:
            # Admin alone is read-only, need manager or staff for management
            if "manager" in user_roles or "staff" in user_roles:
                pass  # Allow archiving
            else:
                raise PermissionError("Admin role alone cannot archive projects. Admin+Manager/Staff required.")
        else:
            # Check if user is owner (non-admin users)
            if not ProjectService.is_project_owner(project_id, user_id):
                raise PermissionError("Only project owners or admin+manager/staff can archive projects")
        
        # Update project status to archived
        result = SupabaseService.update(
            "projects",
            {"status": "archived"},
            {"id": project_id}
        )
        return result

    @staticmethod
    def restore_project(project_id: str, user_id: str) -> Dict[str, Any]:
        """Restore an archived project (owner or admin+manager/staff)"""
        user_roles = ProjectService.get_user_roles(user_id)
        
        # Check if user is admin with additional roles
        if "admin" in user_roles:
            # Admin alone is read-only, need manager or staff for management
            if "manager" in user_roles or "staff" in user_roles:
                pass  # Allow restoring
            else:
                raise PermissionError("Admin role alone cannot restore projects. Admin+Manager/Staff required.")
        else:
            # Check if user is owner (non-admin users)
            if not ProjectService.is_project_owner(project_id, user_id):
                raise PermissionError("Only project owners or admin+manager/staff can restore projects")
        
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
    def update_task_assignees(task_id: str, assignee_ids: List[str], user_id: str) -> Dict[str, Any]:
        """Update task assignees with permission checks:
        - All assignees can add new assignees
        - Only managers can remove assignees
        - Must maintain at least 1 assignee
        """
        # Get current task and assignees
        task = ProjectService.get_task(task_id)
        if not task:
            raise ValueError("Task not found")
        
        current_assignees = set(task.get("assigned", []))
        new_assignees = set(assignee_ids)
        
        # Check if user is trying to remove assignees
        removed_assignees = current_assignees - new_assignees
        
        if removed_assignees:
            # Check if user is a manager
            user_roles = ProjectService.get_user_roles(user_id)
            is_manager = "manager" in user_roles
            
            if not is_manager:
                raise PermissionError("Only managers can remove assignees from tasks")
        
        # Ensure at least one assignee remains
        if len(new_assignees) == 0:
            raise ValueError("At least one assignee is required")
        
        # Check if user is adding assignees (they must be an assignee or manager)
        added_assignees = new_assignees - current_assignees
        if added_assignees:
            user_roles = ProjectService.get_user_roles(user_id)
            is_manager = "manager" in user_roles
            is_current_assignee = user_id in current_assignees
            
            if not (is_manager or is_current_assignee):
                raise PermissionError("Only assignees or managers can add new assignees")
        
        # Validate max 5 assignees
        if len(new_assignees) > 5:
            raise ValueError("Maximum 5 assignees allowed")
        
        return SupabaseService.update("tasks", {"assigned": list(new_assignees)}, {"id": task_id})