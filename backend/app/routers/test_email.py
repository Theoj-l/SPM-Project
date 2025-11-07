"""Test email router for testing email functionality."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from app.services.email_service import EmailService
from app.supabase_client import get_supabase_client

router = APIRouter(prefix="/test-email", tags=["test-email"])

class TestEmailRequest(BaseModel):
    to_email: EmailStr
    test_type: str = "simple"  # simple, task_assigned, deadline, overdue, mention, digest

@router.post("/send")
async def send_test_email(
    request: TestEmailRequest
):
    """Send a test email. Only for testing purposes.
    
    Note: This endpoint is open for testing. In production, consider adding authentication.
    """
    try:
        email_service = EmailService()
        
        if not email_service.smtp_username or not email_service.smtp_password:
            raise HTTPException(
                status_code=500,
                detail="SMTP_USERNAME or SMTP_PASSWORD not configured. Please set them in your .env file."
            )
        
        if request.test_type == "simple":
            subject = "Test Email from SPM"
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }
                    .content { background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Test Email</h1>
                    </div>
                    <div class="content">
                        <p>This is a test email from your SPM application.</p>
                        <p>If you received this, your email configuration is working correctly!</p>
                    </div>
                </div>
            </body>
            </html>
            """
            text_content = "This is a test email from your SPM application. If you received this, your email configuration is working correctly!"
            
            success = email_service.send_email(request.to_email, subject, html_content, text_content)
            
        elif request.test_type == "task_assigned":
            success = email_service.send_task_assigned_email(
                user_email=request.to_email,
                user_name="Test User",
                task_title="Test Task: Review Documentation",
                task_id="test-task-123",
                project_name="Test Project"
            )
            
        elif request.test_type == "deadline":
            success = email_service.send_deadline_reminder_email(
                user_email=request.to_email,
                user_name="Test User",
                task_title="Test Task: Complete Report",
                task_id="test-task-456",
                project_name="Test Project",
                hours_remaining=24
            )
            
        elif request.test_type == "overdue":
            success = email_service.send_overdue_email(
                user_email=request.to_email,
                user_name="Test User",
                task_title="Test Task: Submit Proposal",
                task_id="test-task-789",
                project_name="Test Project"
            )
            
        elif request.test_type == "mention":
            success = email_service.send_mention_email(
                user_email=request.to_email,
                user_name="Test User",
                commenter_name="John Doe",
                task_title="Test Task: Design Review",
                task_id="test-task-321",
                comment_preview="Hey @TestUser, can you take a look at this design? I think we need your input on the color scheme."
            )
            
        elif request.test_type == "digest":
            # Fetch real data from Supabase for the test email
            client = get_supabase_client()
            
            # Find user by email
            user_result = client.table("users").select("id, email, display_name, roles").eq("email", request.to_email).execute()
            
            if not user_result.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"User with email {request.to_email} not found in database"
                )
            
            user = user_result.data[0]
            user_id = user["id"]
            user_email = user.get("email")
            user_name = user.get("display_name") or user.get("email", "").split("@")[0]
            
            now = datetime.utcnow()
            tomorrow = now + timedelta(days=2)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get all projects for mapping
            projects_result = client.table("projects").select("id, name, owner_id, status").execute()
            projects_map = {p["id"]: {"name": p["name"], "owner_id": p.get("owner_id"), "status": p.get("status", "active")} for p in projects_result.data}
            
            # Get all project members for manager role checking
            members_result = client.table("project_members").select("project_id, user_id, role").execute()
            project_members_map = {}
            for member in members_result.data:
                project_id = member["project_id"]
                if project_id not in project_members_map:
                    project_members_map[project_id] = []
                project_members_map[project_id].append({
                    "user_id": member["user_id"],
                    "role": member["role"]
                })
            
            # Get all active tasks
            all_tasks_result = client.table("tasks").select("*").eq("type", "active").execute()
            
            # Get all users info for assignee names
            all_users_result = client.table("users").select("id, display_name, email").execute()
            users_info = {}
            for u in all_users_result.data:
                users_info[u["id"]] = {
                    "display_name": u.get("display_name") or u.get("email", "").split("@")[0],
                    "email": u.get("email")
                }
            
            # Parse user roles (global roles)
            global_roles = user.get("roles", [])
            if isinstance(global_roles, str):
                global_roles = [r.strip().lower() for r in global_roles.split(",")]
            elif isinstance(global_roles, list):
                global_roles = [r.lower() for r in global_roles]
            else:
                global_roles = []
            
            # Check if user is globally a manager/admin/hr
            global_is_manager = "manager" in global_roles or "admin" in global_roles or "hr" in global_roles
            
            # Get relevant projects and tasks based on per-project role
            # User can be manager in one project but staff in another
            relevant_project_ids = set()
            relevant_tasks = []
            project_role_map = {}
            
            # Build a map of projects where user is manager/owner
            manager_project_ids = set()
            for project_id, project_data in projects_map.items():
                if project_data["status"] != "active":
                    continue
                # Check if user is owner
                if project_data.get("owner_id") == user_id:
                    manager_project_ids.add(project_id)
                    project_role_map[project_id] = "manager"
                # Check if user is manager in project_members
                elif project_id in project_members_map:
                    for member in project_members_map[project_id]:
                        if member["user_id"] == user_id and member["role"] in ["owner", "manager"]:
                            manager_project_ids.add(project_id)
                            project_role_map[project_id] = "manager"
                            break
                        elif member["user_id"] == user_id:
                            project_role_map[project_id] = "employee"
                            break
            
            # Collect tasks: if user is manager in a project, get all tasks in that project
            # Otherwise, get only tasks assigned to them
            for task in all_tasks_result.data:
                project_id = task.get("project_id")
                if project_id in manager_project_ids:
                    # User is manager in this project - see all tasks
                    relevant_tasks.append(task)
                    relevant_project_ids.add(project_id)
                else:
                    # User is employee in this project or not a member - only see assigned tasks
                    assigned = task.get("assigned") or []
                    if user_id in assigned:
                        relevant_tasks.append(task)
                        if project_id:
                            relevant_project_ids.add(project_id)
                            if project_id not in project_role_map:
                                project_role_map[project_id] = "employee"
            
            # Determine overall role for email (manager if they manage any project, otherwise employee)
            is_manager = len(manager_project_ids) > 0 or global_is_manager
            
            if not relevant_tasks:
                raise HTTPException(
                    status_code=404,
                    detail=f"No tasks found for user {request.to_email}. Create some tasks first."
                )
            
            # Build digest data
            # 1. Tasks due soon (next 48 hours) and overdue tasks
            tasks_due_soon = []
            overdue_tasks = []
            
            for task in relevant_tasks:
                if not task.get("due_date"):
                    continue
                try:
                    # Handle both date and datetime formats
                    due_date_str = task["due_date"][:10] if isinstance(task["due_date"], str) else task["due_date"].strftime("%Y-%m-%d")
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
                    
                    # Check if overdue (past today)
                    if due_date < today_start and task.get("status") != "completed":
                        overdue_tasks.append({
                            "id": task.get("id"),
                            "title": task.get("title"),
                            "due_date": due_date_str,
                            "project_id": task.get("project_id"),
                            "status": task.get("status"),
                            "assigned": task.get("assigned") or []
                        })
                    # Check if due soon (within next 48 hours)
                    elif today_start <= due_date <= tomorrow:
                        tasks_due_soon.append({
                            "id": task.get("id"),
                            "title": task.get("title"),
                            "due_date": due_date_str,
                            "project_id": task.get("project_id"),
                            "status": task.get("status"),
                            "assigned": task.get("assigned") or []
                        })
                except (ValueError, TypeError) as e:
                    continue
            
            # 2. Status summary
            status_counts = {"todo": 0, "in_progress": 0, "completed": 0, "blocked": 0}
            for task in relevant_tasks:
                status = task.get("status", "todo")
                if status in status_counts:
                    status_counts[status] += 1
            
            total_tasks = len(relevant_tasks)
            completed_tasks = status_counts["completed"]
            completion_percentage = round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)
            
            # Calculate overdue percentage (overdue tasks / total tasks with due dates)
            tasks_with_due_dates = [t for t in relevant_tasks if t.get("due_date")]
            total_tasks_with_due_dates = len(tasks_with_due_dates)
            overdue_percentage = round((len(overdue_tasks) / total_tasks_with_due_dates * 100) if total_tasks_with_due_dates > 0 else 0, 1)
            
            # 3. Per-person task breakdown by project
            person_tasks_by_project = {}
            
            for task in relevant_tasks:
                project_id = task.get("project_id") or "unassigned"
                assigned = task.get("assigned") or []
                
                if project_id not in person_tasks_by_project:
                    person_tasks_by_project[project_id] = {}
                
                for assignee_id in assigned:
                    if assignee_id not in person_tasks_by_project[project_id]:
                        assignee_info = users_info.get(assignee_id, {})
                        person_tasks_by_project[project_id][assignee_id] = {
                            "name": assignee_info.get("display_name", "Unknown"),
                            "tasks": []
                        }
                    
                    person_tasks_by_project[project_id][assignee_id]["tasks"].append({
                        "title": task.get("title", "Untitled"),
                        "status": task.get("status", "todo"),
                        "id": task.get("id")
                    })
            
            # Build projects map for display
            display_projects_map = {}
            for project_id in relevant_project_ids:
                if project_id in projects_map:
                    display_projects_map[project_id] = projects_map[project_id]["name"]
            
            digest_data = {
                "tasks_due_soon": tasks_due_soon,
                "overdue_tasks": overdue_tasks,
                "overdue_percentage": overdue_percentage,
                "status_summary": status_counts,
                "completion_percentage": completion_percentage,
                "total_tasks": total_tasks,
                "person_tasks_by_project": person_tasks_by_project,
                "projects": display_projects_map,
                "is_manager": is_manager
            }
            
            success = email_service.send_daily_digest_email(
                user_email=user_email,
                user_name=user_name,
                digest_data=digest_data
            )
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid test_type. Must be one of: simple, task_assigned, deadline, overdue, mention, digest"
            )
        
        if success:
            return {
                "message": f"Test email sent successfully to {request.to_email}",
                "test_type": request.test_type
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send test email. Check server logs for details."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending test email: {str(e)}")

