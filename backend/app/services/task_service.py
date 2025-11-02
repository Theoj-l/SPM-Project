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
import uuid
from datetime import datetime

class TaskService:
    def __init__(self):
        self.client = get_supabase_client()

    async def get_task_by_id(self, task_id: str, user_id: str, include_archived: bool = False) -> Optional[TaskOut]:
        """Get a specific task by ID with user access validation"""
        try:
            # Get task first
            task_result = self.client.table("tasks").select("*").eq("id", task_id).execute()
            
            if not task_result.data:
                return None

            task_data = task_result.data[0]
            
            # Check if task is archived and if we should include it
            if not include_archived and task_data.get("type") == "archived":
                return None
            
            # Get project information
            project_result = self.client.table("projects").select("id, name, owner_id").eq("id", task_data["project_id"]).execute()
            
            if not project_result.data:
                return None
                
            project = project_result.data[0]
            
            # Check if user has access to this task
            has_access = False
            
            # Check if user is admin first
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
                    # Check if user is a project member
                    members_result = self.client.table("project_members").select("user_id").eq("project_id", project["id"]).execute()
                    for member in members_result.data:
                        if member["user_id"] == user_id:
                            has_access = True
                            break
                    
                    # If not a project member, check if user is assigned to this task
                    if not has_access and task_data.get("assigned"):
                        if user_id in task_data["assigned"]:
                            has_access = True
            
            if not has_access:
                return None

            # Get assignee names
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

            # Prepare update data - only allow certain fields to be updated
            allowed_fields = ['title', 'description', 'status', 'notes', 'assignee_ids']
            update_data = {}
            
            for field in allowed_fields:
                if field in updates:
                    if field == 'assignee_ids':
                        # Map assignee_ids to the database column 'assigned'
                        update_data['assigned'] = updates[field]
                    else:
                        update_data[field] = updates[field]

            if not update_data:
                return task  # No valid updates provided

            # Update the task
            result = self.client.table("tasks").update(update_data).eq("id", task_id).execute()
            
            if result.data:
                # Return the updated task
                return await self.get_task_by_id(task_id, user_id)
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
                comment = CommentOut(
                    id=comment_data["id"],
                    task_id=comment_data["task_id"],
                    user_id=comment_data["user_id"],
                    parent_comment_id=comment_data.get("parent_comment_id"),
                    content=comment_data["content"],
                    created_at=comment_data["created_at"],
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
        """Create a new comment for a task"""
        try:
            # First verify user has access to the task
            task = await self.get_task_by_id(task_id, user_id, include_archived=True)
            if not task:
                raise Exception("Task not found or access denied")

            comment_id = str(uuid.uuid4())
            comment_record = {
                "id": comment_id,
                "task_id": task_id,
                "user_id": user_id,
                "parent_comment_id": comment_data.parent_comment_id,
                "content": comment_data.content,
                "created_at": datetime.utcnow().isoformat()
            }
            
            print(f"Creating comment with parent_comment_id: {comment_data.parent_comment_id}")

            result = self.client.table("task_comments").insert(comment_record).execute()
            
            if result.data:
                # Get user info for the response
                user_result = self.client.table("users").select("email, display_name").eq("id", user_id).execute()
                user_data = user_result.data[0] if user_result.data else {}
                
                return CommentOut(
                    id=comment_id,
                    task_id=task_id,
                    user_id=user_id,
                    parent_comment_id=comment_data.parent_comment_id,
                    content=comment_data.content,
                    created_at=comment_record["created_at"],
                    user_email=user_data.get("email"),
                    user_display_name=user_data.get("display_name") or user_data.get("email", "").split("@")[0]
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
                    uploader_display_name=user_data.get("full_name") or user_data.get("email", "").split("@")[0]
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
                    uploader_display_name=user_data.get("full_name") or user_data.get("email", "").split("@")[0]
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
            except Exception as e:
                error_msg = str(e)
                if "Bucket not found" in error_msg or "bucket" in error_msg.lower():
                    raise Exception(
                        "Storage bucket 'task_file' not found. "
                        "Please create it in Supabase Dashboard: Storage > New Bucket > Name: 'task_file' > Public: ON"
                    )
                raise Exception(f"Failed to upload file to storage: {error_msg}")

            if upload_result.get("error"):
                error_data = upload_result["error"]
                if isinstance(error_data, dict) and error_data.get("message") == "Bucket not found":
                    raise Exception(
                        "Storage bucket 'task_file' not found. "
                        "Please create it in Supabase Dashboard: Storage > New Bucket > Name: 'task_file' > Public: ON"
                    )
                raise Exception(f"Failed to upload file: {upload_result['error']}")

            # Get public URL
            download_url = self.client.storage.from_("task_file").get_public_url(storage_path)

            # Save file metadata to database
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

            result = self.client.table("task_files").insert(file_record).execute()
            
            if result.data:
                # Get user info for the response
                user_result = self.client.table("users").select("email, full_name").eq("id", user_id).execute()
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
            except Exception as e:
                error_msg = str(e)
                if "Bucket not found" in error_msg or "bucket" in error_msg.lower():
                    raise Exception(
                        "Storage bucket 'task_file' not found. "
                        "Please create it in Supabase Dashboard: Storage > New Bucket > Name: 'task_file' > Public: ON"
                    )
                raise Exception(f"Failed to upload file to storage: {error_msg}")

            if upload_result.get("error"):
                error_data = upload_result["error"]
                if isinstance(error_data, dict) and error_data.get("message") == "Bucket not found":
                    raise Exception(
                        "Storage bucket 'task_file' not found. "
                        "Please create it in Supabase Dashboard: Storage > New Bucket > Name: 'task_file' > Public: ON"
                    )
                raise Exception(f"Failed to upload file: {upload_result['error']}")

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
                user_result = self.client.table("users").select("email, full_name").eq("id", user_id).execute()
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
