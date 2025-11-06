from typing import List, Optional, Dict, Any
from app.models.project import (
    TaskOut, 
    CommentCreate, 
    CommentOut, 
    SubTaskCreate, 
    SubTaskOut, 
    FileOut
)
from app.supabase_client import get_supabase_client
from app.services.project_service import ProjectService
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService
from app.models.notification import NotificationCreate
import uuid
from datetime import datetime
import re

class TaskService:
    def __init__(self):
        self.client = get_supabase_client()

    async def get_task_by_id(self, task_id: str, user_id: str, include_archived: bool = False) -> Optional[TaskOut]:
        """Get a specific task by ID with user access validation"""
        try:
            # Optimize: Fetch task, project, user roles, and project membership in parallel where possible
            # Get task first
            task_result = self.client.table("tasks").select("*").eq("id", task_id).execute()
            
            if not task_result.data:
                return None

            task_data = task_result.data[0]
            
            # Check if task is archived and if we should include it
            if not include_archived and task_data.get("type") == "archived":
                return None
            
            project_id = task_data["project_id"]
            
            # Optimize: Fetch project, user roles, and project membership in parallel
            # Use single query to check project membership instead of fetching all members
            project_result = self.client.table("projects").select("id, name, owner_id").eq("id", project_id).execute()
            
            if not project_result.data:
                return None
                
            project = project_result.data[0]
            
            # Check if user has access to this task
            has_access = False
            
            # Check if user is admin or project owner first (fast path)
            user_result = self.client.table("users").select("roles").eq("id", user_id).execute()
            if user_result.data and user_result.data[0].get("roles"):
                user_roles = user_result.data[0]["roles"]
                if "admin" in user_roles:
                    has_access = True
            
            if not has_access:
                # Check if user is project owner
                if project["owner_id"] == user_id:
                    has_access = True
                else:
                    # Optimize: Check project membership with single query instead of fetching all members
                    member_check = self.client.table("project_members").select("user_id").eq("project_id", project_id).eq("user_id", user_id).limit(1).execute()
                    if member_check.data:
                        has_access = True
                    # If not a project member, check if user is assigned to this task
                    elif task_data.get("assigned") and user_id in task_data["assigned"]:
                        has_access = True
            
            if not has_access:
                return None

            # Get assignee names (batch query - already optimized)
            assignee_names = []
            if task_data.get("assigned"):
                users_result = self.client.table("users").select("email, display_name").in_("id", task_data["assigned"]).execute()
                assignee_names = [
                    user.get("display_name") or user.get("email", "").split("@")[0] 
                    for user in users_result.data
                ]

            return TaskOut(
                id=task_data["id"],
                project_id=task_data["project_id"],
                title=task_data["title"],
                description=task_data.get("description"),
                status=task_data["status"],
                due_date=task_data.get("due_date"),
                notes=task_data.get("notes"),
                assignee_ids=task_data.get("assigned", []),
                assignee_names=assignee_names,
                type=task_data.get("type", "active"),  # Default to "active" if type field doesn't exist
                tags=task_data.get("tags", []),
                priority=task_data.get("priority"),
                created_at=task_data.get("created_at")
            )
        except Exception as e:
            print(f"Error getting task: {e}")
            return None

    async def update_task(self, task_id: str, updates: dict, user_id: str) -> Optional[TaskOut]:
        """Update a task with user access validation"""
        try:
            # First check if user has access to the task
            task = await self.get_task_by_id(task_id, user_id)
            if not task:
                return None

            # Check if user can manage tasks (admin alone is read-only)
            user_roles = ProjectService.get_user_roles(user_id)
            can_manage = False
            
            if "admin" in user_roles:
                # Admin alone is read-only, need manager or staff for management
                if "manager" in user_roles or "staff" in user_roles:
                    can_manage = True
            else:
                # Check project membership for non-admin users
                can_manage = ProjectService.can_manage_project(task.project_id, user_id)
            
            if not can_manage:
                raise PermissionError("Admin role alone cannot modify tasks. Admin+Manager/Staff required.")

            # Prevent project_id from being updated
            if 'project_id' in updates:
                raise ValueError("Project cannot be changed after task creation")
            
            # Prepare update data - only allow certain fields to be updated
            allowed_fields = ['title', 'description', 'status', 'notes', 'tags', 'priority']
            update_data = {}
            
            for field in allowed_fields:
                if field in updates:
                    if field == 'tags':
                        # Tags can be updated (already parsed as list if coming from TaskUpdate model)
                        if isinstance(updates[field], list):
                            update_data['tags'] = updates[field]
                        elif isinstance(updates[field], str):
                            # Parse tags from string if needed
                            parsed = [tag.strip() for tag in updates[field].split('#') if tag.strip()]
                            if len(parsed) > 10:
                                raise ValueError('Maximum 10 tags allowed')
                            update_data['tags'] = parsed
                    else:
                        update_data[field] = updates[field]
            
            # Handle assignee_ids separately with permission checks
            if 'assignee_ids' in updates:
                assignee_ids = updates['assignee_ids']
                if not assignee_ids or len(assignee_ids) == 0:
                    raise ValueError('At least one assignee is required')
                
                # Use the same permission logic as update_task_assignees
                current_assignees = set(task.assignee_ids or [])
                new_assignees = set(assignee_ids)
                removed_assignees = current_assignees - new_assignees
                
                if removed_assignees:
                    is_manager = "manager" in user_roles
                    if not is_manager:
                        raise PermissionError("Only managers can remove assignees from tasks")
                
                if len(new_assignees) > 5:
                    raise ValueError("Maximum 5 assignees allowed")
                
                # Check if user is adding assignees
                added_assignees = new_assignees - current_assignees
                if added_assignees:
                    is_manager = "manager" in user_roles
                    is_current_assignee = user_id in current_assignees
                    if not (is_manager or is_current_assignee):
                        raise PermissionError("Only assignees or managers can add new assignees")
                
                update_data['assigned'] = list(new_assignees)

            if not update_data:
                return task  # No valid updates provided

            # Check if status changed for notifications
            old_status = task.status
            status_changed = 'status' in update_data and update_data['status'] != old_status
            
            # Check if assignees changed
            old_assignees = set(task.assignee_ids or [])
            new_assignees = set(updates.get('assignee_ids', task.assignee_ids or []))
            added_assignees = new_assignees - old_assignees
            
            # Update the task
            result = self.client.table("tasks").update(update_data).eq("id", task_id).execute()
            
            if result.data:
                # Return the updated task
                updated_task = await self.get_task_by_id(task_id, user_id)
                
                # Create notifications and send emails for task updates
                if updated_task:
                    notification_service = NotificationService()
                    email_service = EmailService()
                    
                    # Get project name and updater info
                    project_result = self.client.table("projects").select("name").eq("id", updated_task.project_id).execute()
                    project_name = project_result.data[0].get("name", "Unknown Project") if project_result.data else "Unknown Project"
                    
                    updater_result = self.client.table("users").select("email, display_name").eq("id", user_id).execute()
                    updater_data = updater_result.data[0] if updater_result.data else {}
                    updater_name = updater_data.get("display_name") or updater_data.get("email", "").split("@")[0] or "Someone"
                    
                    # Get all assignees (both old and new) to notify
                    all_assignees = updated_task.assignee_ids or []
                    
                    # Determine what was updated
                    updated_fields = []
                    if status_changed:
                        updated_fields.append(("status", {"old_status": old_status, "new_status": update_data['status']}))
                    if 'title' in update_data:
                        updated_fields.append(("title", {"new_title": update_data['title']}))
                    if 'description' in update_data:
                        updated_fields.append(("description", {}))
                    if 'priority' in update_data:
                        updated_fields.append(("priority", {"new_priority": update_data['priority']}))
                    if 'notes' in update_data:
                        updated_fields.append(("notes", {}))
                    if 'tags' in update_data:
                        updated_fields.append(("tags", {"tags": update_data['tags']}))
                    if added_assignees:
                        updated_fields.append(("assignees", {}))
                    
                    # Optimize: Batch fetch all assignee info instead of querying one by one
                    assignees_to_notify = [aid for aid in all_assignees if aid != user_id]
                    assignee_info_map = {}
                    if assignees_to_notify:
                        assignees_result = self.client.table("users").select("id, email, display_name").in_("id", assignees_to_notify).execute()
                        for assignee_data in assignees_result.data or []:
                            assignee_info_map[assignee_data["id"]] = {
                                "email": assignee_data.get("email"),
                                "display_name": assignee_data.get("display_name") or assignee_data.get("email", "").split("@")[0]
                            }
                    
                    # Notify all assignees about updates (except the person making the change)
                    for assignee_id in assignees_to_notify:
                        assignee_info = assignee_info_map.get(assignee_id)
                        if not assignee_info:
                            continue
                        
                        assignee_email = assignee_info["email"]
                        assignee_name = assignee_info["display_name"]
                        
                        # Send notifications and emails for each type of update
                        for update_type, update_details in updated_fields:
                            if update_type == "status":
                                # Status change notification
                                notification_service.create_task_update_notification(
                                    user_id=assignee_id,
                                    task_id=task_id,
                                    task_title=updated_task.title,
                                    old_status=old_status,
                                    new_status=update_data['status'],
                                    project_id=updated_task.project_id
                                )
                                # Send email for status change
                                email_service.send_task_update_email(
                                    user_email=assignee_email,
                                    user_name=assignee_name,
                                    task_title=updated_task.title,
                                    task_id=task_id,
                                    project_name=project_name,
                                    project_id=updated_task.project_id,
                                    updated_by_name=updater_name,
                                    update_type="status",
                                    update_details=update_details
                                )
                            elif update_type == "assignees" and assignee_id in added_assignees:
                                # New assignment notification
                                notification_service.create_task_assigned_notification(
                                    user_id=assignee_id,
                                    task_id=task_id,
                                    task_title=updated_task.title,
                                    project_id=updated_task.project_id
                                )
                                # Send email for new assignment
                                email_service.send_task_assigned_email(
                                    user_email=assignee_email,
                                    user_name=assignee_name,
                                    task_title=updated_task.title,
                                    task_id=task_id,
                                    project_name=project_name,
                                    project_id=updated_task.project_id
                                )
                            else:
                                # Other updates (title, description, priority, notes, tags)
                                # Create general task update notification
                                notification_service.create_notification(
                                    NotificationCreate(
                                        user_id=assignee_id,
                                        type="task_update",
                                        title=f"Task {update_type.title()} Updated",
                                        message=f"Task '{updated_task.title}' {update_type} has been updated by {updater_name}",
                                        link_url=f"/projects/{updated_task.project_id}/tasks/{task_id}",
                                        metadata={
                                            "task_id": task_id,
                                            "project_id": updated_task.project_id,
                                            "update_type": update_type,
                                            **update_details
                                        }
                                    )
                                )
                                # Send email for other updates
                                email_service.send_task_update_email(
                                    user_email=assignee_email,
                                    user_name=assignee_name,
                                    task_title=updated_task.title,
                                    task_id=task_id,
                                    project_name=project_name,
                                    project_id=updated_task.project_id,
                                    updated_by_name=updater_name,
                                    update_type=update_type,
                                    update_details=update_details
                                )
                
                return updated_task
            else:
                return None
                
        except Exception as e:
            print(f"Error updating task: {e}")
            return None

    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task with user access validation"""
        try:
            # First check if user has access to the task
            task = await self.get_task_by_id(task_id, user_id)
            if not task:
                return False

            # Check if user can manage tasks (admin alone is read-only)
            user_roles = ProjectService.get_user_roles(user_id)
            can_manage = False
            
            if "admin" in user_roles:
                # Admin alone is read-only, need manager or staff for management
                if "manager" in user_roles or "staff" in user_roles:
                    can_manage = True
            else:
                # Check project membership for non-admin users
                can_manage = ProjectService.can_manage_project(task.project_id, user_id)
            
            if not can_manage:
                raise PermissionError("Admin role alone cannot delete tasks. Admin+Manager/Staff required.")

            # Delete the task
            result = self.client.table("tasks").delete().eq("id", task_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error deleting task: {e}")
            return False

    async def archive_task(self, task_id: str, user_id: str) -> Optional[TaskOut]:
        """Archive a task with user access validation"""
        try:
            # First check if user has access to the task
            task = await self.get_task_by_id(task_id, user_id)
            if not task:
                return None

            # Check if user can manage tasks (admin alone is read-only)
            user_roles = ProjectService.get_user_roles(user_id)
            can_manage = False
            
            if "admin" in user_roles:
                # Admin alone is read-only, need manager or staff for management
                if "manager" in user_roles or "staff" in user_roles:
                    can_manage = True
            else:
                # Check project membership for non-admin users
                can_manage = ProjectService.can_manage_project(task.project_id, user_id)
            
            if not can_manage:
                raise PermissionError("Admin role alone cannot archive tasks. Admin+Manager/Staff required.")

            # Archive the task by setting type to "archived"
            result = self.client.table("tasks").update({"type": "archived"}).eq("id", task_id).execute()
            
            if result.data:
                # Return updated task
                return await self.get_task_by_id(task_id, user_id, include_archived=True)
            else:
                return None
        except Exception as e:
            print(f"Error archiving task: {e}")
            return None

    async def restore_task(self, task_id: str, user_id: str) -> Optional[TaskOut]:
        """Restore an archived task with user access validation"""
        try:
            # First check if user has access to the task (including archived tasks)
            task = await self.get_task_by_id(task_id, user_id, include_archived=True)
            if not task:
                return None

            # Restore the task by setting type to "active"
            result = self.client.table("tasks").update({"type": "active"}).eq("id", task_id).execute()
            
            if result.data:
                # Return updated task
                return await self.get_task_by_id(task_id, user_id)
            else:
                return None
        except Exception as e:
            print(f"Error restoring task: {e}")
            return None

    # Comments methods
    async def get_task_comments(self, task_id: str, user_id: str) -> List[CommentOut]:
        """Get all comments for a task"""
        try:
            print(f"Loading comments for task {task_id}, user {user_id}")
            # First verify user has access to the task
            task = await self.get_task_by_id(task_id, user_id, include_archived=True)
            if not task:
                print(f"Task {task_id} not found or access denied for user {user_id}")
                return []

            print(f"Querying task_comments table for task {task_id}")
            result = self.client.table("task_comments").select("*").eq("task_id", task_id).order("created_at", desc=False).execute()
            
            print(f"Query result: {result.data}")

            # Get all unique user IDs from comments
            user_ids = list(set([comment["user_id"] for comment in result.data]))
            
            # Fetch user data for all comment authors
            user_data_map = {}
            if user_ids:
                users_result = self.client.table("users").select("id, email, display_name").in_("id", user_ids).execute()
                user_data_map = {user["id"]: user for user in users_result.data}
                print(f"User data map: {user_data_map}")

            # Build comment map
            comment_map = {}
            top_level_comments = []
            
            for comment_data in result.data:
                user_data = user_data_map.get(comment_data["user_id"], {})
                # Ensure created_at has timezone info (append 'Z' if not present)
                created_at = comment_data["created_at"]
                if created_at and not created_at.endswith('Z') and '+' not in created_at:
                    created_at = created_at + 'Z'
                
                comment = CommentOut(
                    id=comment_data["id"],
                    task_id=comment_data["task_id"],
                    user_id=comment_data["user_id"],
                    parent_comment_id=comment_data.get("parent_comment_id"),
                    content=comment_data["content"],
                    created_at=created_at,
                    user_email=user_data.get("email"),
                    user_display_name=user_data.get("display_name") or user_data.get("email", "").split("@")[0],
                    replies=[]
                )
                
                comment_map[comment.id] = comment
                
                # If it's a top-level comment, add to list
                if not comment.parent_comment_id:
                    top_level_comments.append(comment)
            
            # Build nested structure
            for comment in comment_map.values():
                if comment.parent_comment_id and comment.parent_comment_id in comment_map:
                    parent = comment_map[comment.parent_comment_id]
                    if not parent.replies:
                        parent.replies = []
                    parent.replies.append(comment)
                    print(f"Added reply {comment.id} to parent {comment.parent_comment_id}")
            
            print(f"Returning {len(top_level_comments)} top-level comments")
            return top_level_comments
        except Exception as e:
            print(f"Error getting comments: {e}")
            return []

    async def create_comment(self, task_id: str, comment_data: CommentCreate, user_id: str) -> CommentOut:
        """Create a new comment for a task or subtask
        
        Permission rules:
        - Staff can only comment on tasks/subtasks they are assigned to
        - Managers can comment on any tasks/subtasks that belong to their department
        - Admins can comment on any task/subtask
        - For subtasks, check permissions based on the parent task
        """
        try:
            # Check if this is a subtask or a task
            subtask_result = self.client.table("subtasks").select("id, parent_task_id, assigned").eq("id", task_id).execute()
            is_subtask = subtask_result.data and len(subtask_result.data) > 0
            
            if is_subtask:
                # This is a subtask - get parent task for permission checking
                subtask_data = subtask_result.data[0]
                parent_task_id = subtask_data.get("parent_task_id")
                if not parent_task_id:
                    raise Exception("Subtask has no parent task")
                
                # Get parent task for permission checking
                parent_task = await self.get_task_by_id(parent_task_id, user_id, include_archived=True)
                if not parent_task:
                    raise Exception("Parent task not found or access denied")
                
                # Use parent task for permission checks
                task = parent_task
                subtask_assignee_ids = subtask_data.get("assigned", [])
            else:
                # This is a regular task
                task = await self.get_task_by_id(task_id, user_id, include_archived=True)
                if not task:
                    raise Exception("Task not found or access denied")
                subtask_assignee_ids = None
            
            # Get user roles and department (if exists)
            user_result = self.client.table("users").select("id, roles").eq("id", user_id).execute()
            if not user_result.data:
                raise Exception("User not found")
            
            user_data = user_result.data[0]
            user_roles = user_data.get("roles", [])
            if isinstance(user_roles, str):
                user_roles = [r.strip().lower() for r in user_roles.split(",")]
            elif isinstance(user_roles, list):
                user_roles = [r.lower() for r in user_roles]
            
            # Try to get department_id if the column exists (optional)
            user_department_id = None
            try:
                dept_result = self.client.table("users").select("department_id").eq("id", user_id).execute()
                if dept_result.data and dept_result.data[0].get("department_id"):
                    user_department_id = dept_result.data[0].get("department_id")
            except Exception:
                # department_id column doesn't exist, which is fine
                pass
            
            # Admins can always comment
            if "admin" in user_roles:
                pass  # Allow comment
            # Staff can only comment on tasks/subtasks they are assigned to
            elif "staff" in user_roles:
                # For subtasks, check both subtask and parent task assignments
                if is_subtask:
                    is_assigned_to_subtask = subtask_assignee_ids and user_id in subtask_assignee_ids
                    is_assigned_to_task = task.assignee_ids and user_id in task.assignee_ids
                    if not (is_assigned_to_subtask or is_assigned_to_task):
                        raise PermissionError("Staff can only comment on tasks/subtasks they are assigned to")
                else:
                    if not task.assignee_ids or user_id not in task.assignee_ids:
                        raise PermissionError("Staff can only comment on tasks they are assigned to")
            # Managers can comment on tasks (department checking is optional if department_id exists)
            elif "manager" in user_roles:
                # If department_id column exists and both user and project have departments, check them
                if user_department_id is not None:
                    try:
                        # Try to get project's department
                        project_result = self.client.table("projects").select("department_id").eq("id", task.project_id).execute()
                        if project_result.data:
                            project_department_id = project_result.data[0].get("department_id")
                            
                            # If project has no department, manager can comment
                            if not project_department_id:
                                pass  # Allow comment
                            # If manager has no department, they can't comment on department-specific tasks
                            elif not user_department_id:
                                raise PermissionError("Manager must have a department to comment on department tasks")
                            # Check if manager's department matches project's department
                            elif user_department_id != project_department_id:
                                # Check if project's department reports to manager's department
                                try:
                                    dept_result = self.client.table("departments").select("id, parent_department_id").eq("id", project_department_id).execute()
                                    if dept_result.data:
                                        project_dept = dept_result.data[0]
                                        # Check if project department reports to manager's department
                                        if project_dept.get("parent_department_id") != user_department_id:
                                            raise PermissionError("Managers can only comment on tasks in their department")
                                    else:
                                        raise PermissionError("Managers can only comment on tasks in their department")
                                except Exception:
                                    # departments table doesn't exist, just check direct match
                                    raise PermissionError("Managers can only comment on tasks in their department")
                    except Exception as dept_err:
                        # If department_id column doesn't exist in projects table, allow manager to comment
                        if "column" in str(dept_err).lower() and "does not exist" in str(dept_err).lower():
                            pass  # Allow comment - no department system
                        else:
                            raise
                else:
                    # No department_id column in users table - managers can comment on any task
                    pass  # Allow comment
            else:
                # User has no recognized role - deny by default
                raise PermissionError("User does not have permission to comment on tasks")

            comment_id = str(uuid.uuid4())
            # Use UTC timezone-aware datetime and append 'Z' to indicate UTC
            utc_now = datetime.utcnow()
            created_at_str = utc_now.isoformat() + 'Z'
            comment_record = {
                "id": comment_id,
                "task_id": task_id,
                "user_id": user_id,
                "parent_comment_id": comment_data.parent_comment_id,
                "content": comment_data.content,
                "created_at": created_at_str
            }
            
            print(f"Creating comment with parent_comment_id: {comment_data.parent_comment_id}")

            result = self.client.table("task_comments").insert(comment_record).execute()
            
            if result.data:
                # Get user info for the response
                user_result = self.client.table("users").select("email, display_name").eq("id", user_id).execute()
                user_data = user_result.data[0] if user_result.data else {}
                commenter_name = user_data.get("display_name") or user_data.get("email", "").split("@")[0]
                
                # Notify all task assignees about the new comment (except the commenter)
                # Wrap in try-catch so notification failures don't prevent comment creation
                try:
                    notification_service = NotificationService()
                    project_result = self.client.table("projects").select("name").eq("id", task.project_id).execute()
                    project_name = project_result.data[0].get("name", "Unknown Project") if project_result.data else "Unknown Project"
                    
                    # Get all assignees for the task
                    assignee_ids = task.assignee_ids or []
                    for assignee_id in assignee_ids:
                        if assignee_id != user_id:  # Don't notify the commenter
                            try:
                                notification_service.create_notification(
                                    NotificationCreate(
                                        user_id=assignee_id,
                                        type="task_update",
                                        title="New Comment",
                                        message=f"{commenter_name} commented on task '{task.title}'",
                                        link_url=f"/projects/{task.project_id}/tasks/{task_id}",
                                        metadata={
                                            "task_id": task_id,
                                            "project_id": task.project_id,
                                            "comment_id": comment_id,
                                            "commenter_id": user_id,
                                            "update_type": "comment"
                                        }
                                    )
                                )
                            except Exception as notif_err:
                                print(f"Failed to create notification for assignee {assignee_id}: {notif_err}")
                                # Continue with other notifications
                except Exception as notif_err:
                    print(f"Error creating comment notifications: {notif_err}")
                    # Continue - don't fail comment creation if notifications fail
                
                # Check for @mentions in comment
                # Pattern matches @username or @display name (handles spaces and common characters)
                mention_pattern = r'@([\w\s]+?)(?=\s|$|[.,!?;:])'
                mentions = re.findall(mention_pattern, comment_data.content)
                # Clean up mentions (remove trailing spaces, normalize)
                mentions = [m.strip().lower() for m in mentions if m.strip()]
                
                # Check for @mentions in comment (wrap in try-catch so failures don't prevent comment creation)
                try:
                    if mentions:
                        # Get all users to find matches
                        all_users_result = self.client.table("users").select("id, email, display_name").execute()
                        users_by_email = {user.get("email", "").split("@")[0]: user for user in all_users_result.data}
                        users_by_display_name = {user.get("display_name", "").lower(): user for user in all_users_result.data if user.get("display_name")}
                        
                        notification_service = NotificationService()
                        email_service = EmailService()
                        
                        project_result = self.client.table("projects").select("name").eq("id", task.project_id).execute()
                        project_name = project_result.data[0].get("name", "Unknown Project") if project_result.data else "Unknown Project"
                        
                        mentioned_user_ids = set()
                        for mention in mentions:
                            # Try to match by email username or display name
                            mentioned_user = None
                            mention_lower = mention.lower()
                            
                            # Check email username
                            if mention_lower in users_by_email:
                                mentioned_user = users_by_email[mention_lower]
                            # Check display name
                            elif mention_lower in users_by_display_name:
                                mentioned_user = users_by_display_name[mention_lower]
                            
                            if mentioned_user and mentioned_user["id"] != user_id:
                                mentioned_user_id = mentioned_user["id"]
                                if mentioned_user_id not in mentioned_user_ids:
                                    mentioned_user_ids.add(mentioned_user_id)
                                    
                                    try:
                                        # Create in-app notification
                                        notification_service.create_mention_notification(
                                            mentioned_user_id=mentioned_user_id,
                                            commenter_user_id=user_id,
                                            commenter_name=commenter_name,
                                            task_id=task_id,
                                            task_title=task.title,
                                            comment_preview=comment_data.content[:200],
                                            project_id=task.project_id
                                        )
                                    except Exception as notif_err:
                                        print(f"Failed to create mention notification for {mentioned_user_id}: {notif_err}")
                                    
                                    try:
                                        # Send email notification
                                        email_service.send_mention_email(
                                            user_email=mentioned_user.get("email"),
                                            user_name=mentioned_user.get("display_name") or mentioned_user.get("email", "").split("@")[0],
                                            commenter_name=commenter_name,
                                            task_title=task.title,
                                            task_id=task_id,
                                            comment_preview=comment_data.content[:200],
                                            project_id=task.project_id
                                        )
                                    except Exception as email_err:
                                        print(f"Failed to send mention email to {mentioned_user.get('email')}: {email_err}")
                except Exception as mention_err:
                    print(f"Error processing mentions: {mention_err}")
                    # Continue - don't fail comment creation if mention processing fails
                
                # Ensure created_at has timezone info (should already have 'Z' from above, but double-check)
                created_at = comment_record["created_at"]
                if created_at and not created_at.endswith('Z') and '+' not in created_at:
                    created_at = created_at + 'Z'
                
                return CommentOut(
                    id=comment_id,
                    task_id=task_id,
                    user_id=user_id,
                    parent_comment_id=comment_data.parent_comment_id,
                    content=comment_data.content,
                    created_at=created_at,
                    user_email=user_data.get("email"),
                    user_display_name=commenter_name
                )
            else:
                raise Exception("Failed to create comment")
        except Exception as e:
            print(f"Error creating comment: {e}")
            raise e

    async def delete_comment(self, comment_id: str, user_id: str) -> bool:
        """Delete a comment (only by the comment author)"""
        try:
            result = self.client.table("task_comments").delete().eq("id", comment_id).eq("user_id", user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error deleting comment: {e}")
            return False

    # Sub-tasks methods
    async def get_subtasks(self, task_id: str, user_id: str) -> List[SubTaskOut]:
        """Get all sub-tasks for a task"""
        try:
            # First verify user has access to the parent task
            task = await self.get_task_by_id(task_id, user_id, include_archived=True)
            if not task:
                return []

            result = self.client.table("subtasks").select("*").eq("parent_task_id", task_id).order("created_at", desc=False).execute()

            subtasks = []
            for subtask_data in result.data:
                # Get assignee names
                assignee_names = []
                assigned_ids = subtask_data.get("assigned", [])
                if assigned_ids:
                    users_result = self.client.table("users").select("email, display_name").in_("id", assigned_ids).execute()
                    assignee_names = [
                        user.get("display_name") or user.get("email", "").split("@")[0] 
                        for user in users_result.data
                    ]

                subtasks.append(SubTaskOut(
                    id=subtask_data["id"],
                    title=subtask_data["title"],
                    description=subtask_data.get("description"),
                    parent_task_id=subtask_data["parent_task_id"],
                    status=subtask_data["status"],
                    assignee_ids=assigned_ids,  # Map assigned back to assignee_ids
                    assignee_names=assignee_names,
                    due_date=subtask_data.get("due_date"),
                    notes=subtask_data.get("notes"),
                    tags=subtask_data.get("tags", []),
                    created_at=subtask_data.get("created_at")
                ))
            
            return subtasks
        except Exception as e:
            print(f"Error getting subtasks: {e}")
            return []

    async def get_subtask_by_id(self, subtask_id: str, user_id: str) -> Optional[SubTaskOut]:
        """Get a specific sub-task by ID"""
        try:
            result = self.client.table("subtasks").select("*").eq("id", subtask_id).execute()
            
            if not result.data:
                return None
            
            subtask_data = result.data[0]
            
            # Get the parent task to verify access
            parent_task = await self.get_task_by_id(subtask_data["parent_task_id"], user_id, include_archived=True)
            if not parent_task:
                return None
            
            # Get assignee names
            assignee_names = []
            assigned_ids = subtask_data.get("assigned", [])
            if assigned_ids:
                users_result = self.client.table("users").select("email, display_name").in_("id", assigned_ids).execute()
                assignee_names = [
                    user.get("display_name") or user.get("email", "").split("@")[0] 
                    for user in users_result.data
                ]

            return SubTaskOut(
                id=subtask_data["id"],
                title=subtask_data["title"],
                description=subtask_data.get("description"),
                parent_task_id=subtask_data["parent_task_id"],
                status=subtask_data["status"],
                assignee_ids=assigned_ids,  # Map assigned back to assignee_ids
                assignee_names=assignee_names,
                due_date=subtask_data.get("due_date"),
                notes=subtask_data.get("notes"),
                tags=subtask_data.get("tags", []),
                created_at=subtask_data.get("created_at")
            )
        except Exception as e:
            print(f"Error getting subtask by ID: {e}")
            return None

    async def create_subtask(self, task_id: str, subtask_data: SubTaskCreate, user_id: str) -> SubTaskOut:
        """Create a new sub-task"""
        try:
            # First verify user has access to the parent task
            task = await self.get_task_by_id(task_id, user_id, include_archived=True)
            if not task:
                raise Exception("Parent task not found or access denied")

            subtask_id = str(uuid.uuid4())
            subtask_record = {
                "id": subtask_id,
                "title": subtask_data.title,
                "description": subtask_data.description,
                "parent_task_id": task_id,
                "status": subtask_data.status,
                "assigned": subtask_data.assignee_ids or [],  # Map assignee_ids to assigned
                "due_date": subtask_data.due_date,
                "notes": subtask_data.notes,
                "tags": subtask_data.tags or [],
                "created_at": datetime.utcnow().isoformat()
            }

            result = self.client.table("subtasks").insert(subtask_record).execute()
            
            if result.data:
                # Get assignee names
                assignee_names = []
                if subtask_data.assignee_ids:
                    users_result = self.client.table("users").select("email, display_name").in_("id", subtask_data.assignee_ids).execute()
                    assignee_names = [
                        user.get("display_name") or user.get("email", "").split("@")[0] 
                        for user in users_result.data
                    ]

                return SubTaskOut(
                    id=subtask_id,
                    title=subtask_data.title,
                    description=subtask_data.description,
                    parent_task_id=task_id,
                    status=subtask_data.status,
                    assignee_ids=subtask_data.assignee_ids or [],
                    assignee_names=assignee_names,
                    due_date=subtask_data.due_date,
                    notes=subtask_data.notes,
                    tags=subtask_data.tags or [],
                    created_at=subtask_record["created_at"]
                )
            else:
                raise Exception("Failed to create subtask")
        except Exception as e:
            print(f"Error creating subtask: {e}")
            raise e

    async def update_subtask(self, subtask_id: str, updates: dict, user_id: str) -> Optional[SubTaskOut]:
        """Update a sub-task"""
        try:
            # First get the subtask to verify access through parent task
            subtask_result = self.client.table("subtasks").select("parent_task_id").eq("id", subtask_id).execute()
            if not subtask_result.data:
                return None

            parent_task_id = subtask_result.data[0]["parent_task_id"]
            task = await self.get_task_by_id(parent_task_id, user_id, include_archived=True)
            if not task:
                return None

            # Validate assignee_ids if being updated
            if "assignee_ids" in updates or "assigned" in updates:
                assignee_ids = updates.get("assignee_ids") or updates.get("assigned")
                if not assignee_ids or len(assignee_ids) == 0:
                    raise ValueError('At least one assignee is required')
                # Map assignee_ids to assigned if needed
                if "assignee_ids" in updates:
                    updates["assigned"] = updates.pop("assignee_ids")

            # Update the subtask
            result = self.client.table("subtasks").update(updates).eq("id", subtask_id).execute()
            
            if result.data:
                subtask_data = result.data[0]
                # Get assignee names
                assignee_names = []
                if subtask_data.get("assignee_ids"):
                    users_result = self.client.table("users").select("email, display_name").in_("id", subtask_data["assignee_ids"]).execute()
                    assignee_names = [
                        user.get("display_name") or user.get("email", "").split("@")[0] 
                        for user in users_result.data
                    ]

                return SubTaskOut(
                    id=subtask_data["id"],
                    title=subtask_data["title"],
                    description=subtask_data.get("description"),
                    parent_task_id=subtask_data["parent_task_id"],
                    status=subtask_data["status"],
                    assignee_ids=subtask_data.get("assignee_ids", []),
                    assignee_names=assignee_names,
                    created_at=subtask_data.get("created_at")
                )
            else:
                return None
        except Exception as e:
            print(f"Error updating subtask: {e}")
            return None

    async def delete_subtask(self, subtask_id: str, user_id: str) -> bool:
        """Delete a sub-task"""
        try:
            # First get the subtask to verify access through parent task
            subtask_result = self.client.table("subtasks").select("parent_task_id").eq("id", subtask_id).execute()
            if not subtask_result.data:
                return False

            parent_task_id = subtask_result.data[0]["parent_task_id"]
            task = await self.get_task_by_id(parent_task_id, user_id, include_archived=True)
            if not task:
                return False

            result = self.client.table("subtasks").delete().eq("id", subtask_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error deleting subtask: {e}")
            return False

    # File methods
    async def get_task_files(self, task_id: str, user_id: str) -> List[FileOut]:
        """Get all files for a task"""
        try:
            # First verify user has access to the task
            task = await self.get_task_by_id(task_id, user_id, include_archived=True)
            if not task:
                return []

            result = self.client.table("task_files").select("""
                *,
                users!inner(email, display_name)
            """).eq("task_id", task_id).order("created_at", desc=False).execute()

            files = []
            for file_data in result.data:
                user_data = file_data.get("users", {})
                files.append(FileOut(
                    id=file_data["id"],
                    filename=file_data["filename"],
                    original_filename=file_data["original_filename"],
                    content_type=file_data["content_type"],
                    file_size=file_data["file_size"],
                    task_id=file_data.get("task_id"),
                    subtask_id=file_data.get("subtask_id"),
                    uploaded_by=file_data["uploaded_by"],
                    created_at=file_data["created_at"],
                    download_url=file_data.get("download_url"),
                    uploader_email=user_data.get("email"),
                    uploader_display_name=user_data.get("display_name") or user_data.get("email", "").split("@")[0]
                ))
            
            return files
        except Exception as e:
            print(f"Error getting files: {e}")
            return []

    async def get_subtask_files(self, subtask_id: str, user_id: str) -> List[FileOut]:
        """Get all files for a subtask"""
        try:
            # First verify user has access to the subtask
            subtask = await self.get_subtask_by_id(subtask_id, user_id)
            if not subtask:
                return []

            result = self.client.table("task_files").select("""
                *,
                users!inner(email, display_name)
            """).eq("subtask_id", subtask_id).order("created_at", desc=False).execute()

            files = []
            for file_data in result.data:
                user_data = file_data.get("users", {})
                files.append(FileOut(
                    id=file_data["id"],
                    filename=file_data["filename"],
                    original_filename=file_data["original_filename"],
                    content_type=file_data["content_type"],
                    file_size=file_data["file_size"],
                    task_id=file_data.get("task_id"),
                    subtask_id=file_data.get("subtask_id"),
                    uploaded_by=file_data["uploaded_by"],
                    created_at=file_data["created_at"],
                    download_url=file_data.get("download_url"),
                    uploader_email=user_data.get("email"),
                    uploader_display_name=user_data.get("display_name") or user_data.get("email", "").split("@")[0]
                ))
            
            return files
        except Exception as e:
            print(f"Error getting subtask files: {e}")
            return []

    async def upload_file(self, task_id: str, filename: str, content_type: str, file_content: bytes, user_id: str) -> FileOut:
        """Upload a file to a task"""
        try:
            # First verify user has access to the task
            task = await self.get_task_by_id(task_id, user_id, include_archived=True)
            if not task:
                raise Exception("Task not found or access denied")

            file_id = str(uuid.uuid4())
            
            # Upload to Supabase Storage (path is relative to bucket)
            storage_path = f"{task_id}/{file_id}_{filename}"
            try:
                upload_result = self.client.storage.from_("task_file").upload(storage_path, file_content, {
                    "content-type": content_type
                })
                
                # Check if upload_result is a Response-like object with error attribute
                if hasattr(upload_result, 'error') and upload_result.error:
                    error_data = upload_result.error
                    if isinstance(error_data, dict):
                        error_msg = error_data.get("message", str(error_data))
                    else:
                        error_msg = str(error_data)
                    
                    if "Bucket not found" in error_msg or "bucket" in error_msg.lower():
                        raise Exception(
                            "Storage bucket 'task_file' not found. "
                            "Please create it in Supabase Dashboard: Storage > New Bucket > Name: 'task_file' > Public: ON"
                        )
                    # Check for RLS errors
                    if "row-level security" in error_msg.lower() or "rls" in error_msg.lower() or "unauthorized" in error_msg.lower():
                        raise Exception(
                            f"Storage RLS policy violation: {error_msg}. "
                            "The storage bucket 'task_file' has RLS policies that are blocking uploads. "
                            "Please check: 1) SUPABASE_SERVICE_KEY is set correctly, "
                            "2) Storage bucket RLS policies allow service role uploads, "
                            "3) In Supabase Dashboard: Storage > task_file > Policies > ensure service role can INSERT"
                        )
                    raise Exception(f"Failed to upload file to storage: {error_msg}")
                    
            except Exception as e:
                error_msg = str(e)
                if "Bucket not found" in error_msg or "bucket" in error_msg.lower():
                    raise Exception(
                        "Storage bucket 'task_file' not found. "
                        "Please create it in Supabase Dashboard: Storage > New Bucket > Name: 'task_file' > Public: ON"
                    )
                # Check for RLS errors in exception
                if "row-level security" in error_msg.lower() or "rls" in error_msg.lower() or "unauthorized" in error_msg.lower():
                    raise Exception(
                        f"Storage RLS policy violation: {error_msg}. "
                        "The storage bucket 'task_file' has RLS policies that are blocking uploads. "
                        "Please check: 1) SUPABASE_SERVICE_KEY is set correctly, "
                        "2) Storage bucket RLS policies allow service role uploads, "
                        "3) In Supabase Dashboard: Storage > task_file > Policies > ensure service role can INSERT"
                    )
                raise Exception(f"Failed to upload file to storage: {error_msg}")

            # Get public URL
            download_url = self.client.storage.from_("task_file").get_public_url(storage_path)

            # Save file metadata to database
            # Use service role client to bypass RLS
            file_record = {
                "id": file_id,
                "filename": storage_path,
                "original_filename": filename,
                "content_type": content_type,
                "file_size": len(file_content),
                "task_id": task_id,
                "uploaded_by": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "download_url": download_url
            }

            # Insert with service role (should bypass RLS)
            # If this still fails, the RLS policy might need to be updated
            result = self.client.table("task_files").insert(file_record).execute()
            
            # Check for RLS errors
            if result.data is None and hasattr(result, 'error') and result.error:
                error_msg = str(result.error)
                if "row-level security" in error_msg.lower() or "rls" in error_msg.lower():
                    raise Exception(
                        f"RLS policy violation: {error_msg}. "
                        "The service role key should bypass RLS. "
                        "Please check: 1) SUPABASE_SERVICE_KEY is set correctly, "
                        "2) RLS policies on task_files table allow service role inserts, "
                        "3) The service role key has proper permissions."
                    )
            
            if result.data:
                # Get user info for the response
                user_result = self.client.table("users").select("email, display_name").eq("id", user_id).execute()
                user_data = user_result.data[0] if user_result.data else {}
                
                return FileOut(
                    id=file_id,
                    filename=storage_path,
                    original_filename=filename,
                    content_type=content_type,
                    file_size=len(file_content),
                    task_id=task_id,
                    subtask_id=None,
                    uploaded_by=user_id,
                    created_at=file_record["created_at"],
                    download_url=download_url,
                    uploader_email=user_data.get("email"),
                    # Use display_name (fallback to email username)
                    uploader_display_name=user_data.get("display_name") or user_data.get("email", "").split("@")[0]
                )
            else:
                raise Exception("Failed to save file metadata")
        except Exception as e:
            print(f"Error uploading file: {e}")
            raise e

    async def upload_subtask_file(self, subtask_id: str, filename: str, content_type: str, file_content: bytes, user_id: str) -> FileOut:
        """Upload a file to a subtask"""
        try:
            # First verify user has access to the subtask
            subtask = await self.get_subtask_by_id(subtask_id, user_id)
            if not subtask:
                raise Exception("Subtask not found or access denied")

            file_id = str(uuid.uuid4())
            
            # Upload to Supabase Storage (store under parent task, path is relative to bucket)
            parent_task_id = subtask.parent_task_id
            storage_path = f"{parent_task_id}/{subtask_id}/{file_id}_{filename}"
            try:
                upload_result = self.client.storage.from_("task_file").upload(storage_path, file_content, {
                    "content-type": content_type
                })
                
                # Check if upload_result is a Response-like object with error attribute
                if hasattr(upload_result, 'error') and upload_result.error:
                    error_data = upload_result.error
                    if isinstance(error_data, dict):
                        error_msg = error_data.get("message", str(error_data))
                    else:
                        error_msg = str(error_data)
                    
                    if "Bucket not found" in error_msg or "bucket" in error_msg.lower():
                        raise Exception(
                            "Storage bucket 'task_file' not found. "
                            "Please create it in Supabase Dashboard: Storage > New Bucket > Name: 'task_file' > Public: ON"
                        )
                    # Check for RLS errors
                    if "row-level security" in error_msg.lower() or "rls" in error_msg.lower() or "unauthorized" in error_msg.lower():
                        raise Exception(
                            f"Storage RLS policy violation: {error_msg}. "
                            "The storage bucket 'task_file' has RLS policies that are blocking uploads. "
                            "Please check: 1) SUPABASE_SERVICE_KEY is set correctly, "
                            "2) Storage bucket RLS policies allow service role uploads, "
                            "3) In Supabase Dashboard: Storage > task_file > Policies > ensure service role can INSERT"
                        )
                    raise Exception(f"Failed to upload file to storage: {error_msg}")
                    
            except Exception as e:
                error_msg = str(e)
                if "Bucket not found" in error_msg or "bucket" in error_msg.lower():
                    raise Exception(
                        "Storage bucket 'task_file' not found. "
                        "Please create it in Supabase Dashboard: Storage > New Bucket > Name: 'task_file' > Public: ON"
                    )
                # Check for RLS errors in exception
                if "row-level security" in error_msg.lower() or "rls" in error_msg.lower() or "unauthorized" in error_msg.lower():
                    raise Exception(
                        f"Storage RLS policy violation: {error_msg}. "
                        "The storage bucket 'task_file' has RLS policies that are blocking uploads. "
                        "Please check: 1) SUPABASE_SERVICE_KEY is set correctly, "
                        "2) Storage bucket RLS policies allow service role uploads, "
                        "3) In Supabase Dashboard: Storage > task_file > Policies > ensure service role can INSERT"
                    )
                raise Exception(f"Failed to upload file to storage: {error_msg}")

            # Get public URL
            download_url = self.client.storage.from_("task_file").get_public_url(storage_path)

            # Save file metadata to database
            file_record = {
                "id": file_id,
                "filename": storage_path,
                "original_filename": filename,
                "content_type": content_type,
                "file_size": len(file_content),
                "task_id": parent_task_id,
                "subtask_id": subtask_id,
                "uploaded_by": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "download_url": download_url
            }

            result = self.client.table("task_files").insert(file_record).execute()
            
            if result.data:
                # Get user info for the response
                user_result = self.client.table("users").select("email, display_name").eq("id", user_id).execute()
                user_data = user_result.data[0] if user_result.data else {}
                
                return FileOut(
                    id=file_id,
                    filename=storage_path,
                    original_filename=filename,
                    content_type=content_type,
                    file_size=len(file_content),
                    task_id=parent_task_id,
                    subtask_id=subtask_id,
                    uploaded_by=user_id,
                    created_at=file_record["created_at"],
                    download_url=download_url,
                    uploader_email=user_data.get("email"),
                    uploader_display_name=user_data.get("display_name") or user_data.get("email", "").split("@")[0]
                )
            else:
                raise Exception("Failed to save file metadata")
        except Exception as e:
            print(f"Error uploading subtask file: {e}")
            raise e

    async def download_file(self, file_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Download a file"""
        try:
            # Get file info first
            file_result = self.client.table("task_files").select("*").eq("id", file_id).execute()
            if not file_result.data:
                return None
            
            file_data = file_result.data[0]
            
            # Verify user has access - check task or subtask
            if file_data.get("subtask_id"):
                subtask = await self.get_subtask_by_id(file_data["subtask_id"], user_id)
                if not subtask:
                    return None
            else:
                task = await self.get_task_by_id(file_data["task_id"], user_id, include_archived=True)
                if not task:
                    return None
            
            # Download file content from Supabase Storage
            storage_path = file_data["filename"]
            file_content = self.client.storage.from_("task_file").download(storage_path)
            # Some client versions return bytes directly; ensure we have bytes
            if isinstance(file_content, dict) and file_content.get("error"):
                raise Exception(f"Failed to download file: {file_content['error']}")
            
            return {
                "filename": file_data["original_filename"],
                "content_type": file_data["content_type"],
                "content": file_content
            }
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None

    async def delete_file(self, file_id: str, user_id: str) -> bool:
        """Delete a file (only by the uploader)"""
        try:
            # Get file info first
            file_result = self.client.table("task_files").select("filename, uploaded_by").eq("id", file_id).execute()
            if not file_result.data:
                return False

            file_data = file_result.data[0]
            if file_data["uploaded_by"] != user_id:
                return False  # Only the uploader can delete

            # Delete from storage
            self.client.storage.from_("task_file").remove([file_data["filename"]])

            # Delete from database
            result = self.client.table("task_files").delete().eq("id", file_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
