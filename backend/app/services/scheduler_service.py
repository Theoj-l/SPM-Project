"""Scheduler service for scheduled notifications."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.supabase_client import get_supabase_client
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService

class SchedulerService:
    """Service for scheduling periodic tasks."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.client = get_supabase_client()
        self.notification_service = NotificationService()
        self.email_service = EmailService()
    
    def start(self):
        """Start the scheduler."""
        # Check deadline reminders every hour
        self.scheduler.add_job(
            self.check_deadline_reminders,
            trigger=CronTrigger(minute=0),  # Run at the top of every hour
            id="deadline_reminders",
            replace_existing=True
        )
        
        # Check overdue tasks every hour
        self.scheduler.add_job(
            self.check_overdue_tasks,
            trigger=CronTrigger(minute=0),  # Run at the top of every hour
            id="overdue_tasks",
            replace_existing=True
        )
        
        # Send daily digests at 5 PM SGT (9 AM UTC)
        self.scheduler.add_job(
            self.send_daily_digests,
            trigger=CronTrigger(hour=9, minute=0),  # 5 PM SGT = 9 AM UTC
            id="daily_digests",
            replace_existing=True
        )
        
        self.scheduler.start()
        print("✅ Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
    
    async def check_deadline_reminders(self):
        """Check for tasks with deadlines approaching (24 hours)."""
        try:
            now = datetime.utcnow()
            reminder_time = now + timedelta(hours=24)
            
            # Get tasks with due_date between now and 24 hours from now
            # Format: YYYY-MM-DD
            due_date_str = reminder_time.strftime("%Y-%m-%d")
            today_str = now.strftime("%Y-%m-%d")
            
            # Query tasks due in next 24 hours
            result = self.client.table("tasks").select("*").eq("type", "active").in_("status", ["todo", "in_progress", "blocked"]).execute()
            
            tasks_to_notify = []
            for task in result.data:
                if not task.get("due_date"):
                    continue
                
                try:
                    due_date = datetime.strptime(task["due_date"][:10], "%Y-%m-%d")  # Get date part
                    hours_until_due = (due_date - now).total_seconds() / 3600
                    
                    # Notify if between 23 and 25 hours remaining (within 1 hour window)
                    if 23 <= hours_until_due <= 25:
                        # Check if we already sent a reminder (store in metadata or track separately)
                        tasks_to_notify.append((task, hours_until_due))
                except (ValueError, TypeError):
                    continue
            
            # Send notifications and emails
            for task, hours_remaining in tasks_to_notify:
                assignee_ids = task.get("assigned") or []
                if not assignee_ids:
                    continue
                
                project_result = self.client.table("projects").select("name").eq("id", task.get("project_id")).execute()
                project_name = project_result.data[0].get("name", "Unknown Project") if project_result.data else "Unknown Project"
                
                for assignee_id in assignee_ids:
                    # Get user info
                    user_result = self.client.table("users").select("email, display_name").eq("id", assignee_id).execute()
                    if not user_result.data:
                        continue
                    
                    user_data = user_result.data[0]
                    user_email = user_data.get("email")
                    user_name = user_data.get("display_name") or user_data.get("email", "").split("@")[0]
                    
                    # Send email
                    self.email_service.send_deadline_reminder_email(
                        user_email=user_email,
                        user_name=user_name,
                        task_title=task.get("title"),
                        task_id=task.get("id"),
                        project_name=project_name,
                        hours_remaining=int(hours_remaining)
                    )
            
            print(f"Checked deadline reminders: {len(tasks_to_notify)} tasks need reminders")
        except Exception as e:
            print(f"Error checking deadline reminders: {e}")
    
    async def check_overdue_tasks(self):
        """Check for tasks that are overdue (24 hours past deadline)."""
        try:
            now = datetime.utcnow()
            overdue_threshold = now - timedelta(hours=24)
            
            # Query active tasks that are not completed
            result = self.client.table("tasks").select("*").eq("type", "active").in_("status", ["todo", "in_progress", "blocked"]).execute()
            
            overdue_tasks = []
            for task in result.data:
                if not task.get("due_date"):
                    continue
                
                try:
                    due_date = datetime.strptime(task["due_date"][:10], "%Y-%m-%d")
                    
                    # Check if overdue by more than 24 hours but less than 48 hours
                    hours_overdue = (now - due_date).total_seconds() / 3600
                    if 24 <= hours_overdue <= 48 and due_date < now:
                        overdue_tasks.append(task)
                except (ValueError, TypeError):
                    continue
            
            # Send notifications and emails
            for task in overdue_tasks:
                assignee_ids = task.get("assigned") or []
                if not assignee_ids:
                    continue
                
                project_result = self.client.table("projects").select("name").eq("id", task.get("project_id")).execute()
                project_name = project_result.data[0].get("name", "Unknown Project") if project_result.data else "Unknown Project"
                
                for assignee_id in assignee_ids:
                    # Get user info
                    user_result = self.client.table("users").select("email, display_name").eq("id", assignee_id).execute()
                    if not user_result.data:
                        continue
                    
                    user_data = user_result.data[0]
                    user_email = user_data.get("email")
                    user_name = user_data.get("display_name") or user_data.get("email", "").split("@")[0]
                    
                    # Create notification
                    from app.models.notification import NotificationCreate
                    self.notification_service.create_notification(
                        NotificationCreate(
                            user_id=assignee_id,
                            type="overdue",
                            title="Task Overdue",
                            message=f"Task '{task.get('title')}' is now overdue",
                            link_url=f"/projects/{task.get('project_id')}/tasks/{task.get('id')}" if task.get('project_id') else f"/tasks/{task.get('id')}",
                            metadata={
                                "task_id": task.get("id"),
                                "project_id": task.get("project_id")
                            }
                        )
                    )
                    
                    # Send email
                    self.email_service.send_overdue_email(
                        user_email=user_email,
                        user_name=user_name,
                        task_title=task.get("title"),
                        task_id=task.get("id"),
                        project_name=project_name
                    )
            
            print(f"Checked overdue tasks: {len(overdue_tasks)} overdue tasks found")
        except Exception as e:
            print(f"Error checking overdue tasks: {e}")
    
    async def send_daily_digests(self):
        """Send daily digest emails to all users (managers and employees) with role-based content."""
        try:
            # Get all users
            users_result = self.client.table("users").select("id, email, display_name, roles").execute()
            
            now = datetime.utcnow()
            tomorrow = now + timedelta(days=2)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get all projects for mapping
            projects_result = self.client.table("projects").select("id, name, owner_id, status").execute()
            projects_map = {p["id"]: {"name": p["name"], "owner_id": p.get("owner_id"), "status": p.get("status", "active")} for p in projects_result.data}
            
            # Get all project members for manager role checking
            members_result = self.client.table("project_members").select("project_id, user_id, role").execute()
            project_members_map = {}  # {project_id: [{user_id, role}]}
            for member in members_result.data:
                project_id = member["project_id"]
                if project_id not in project_members_map:
                    project_members_map[project_id] = []
                project_members_map[project_id].append({
                    "user_id": member["user_id"],
                    "role": member["role"]
                })
            
            # Get all active tasks
            all_tasks_result = self.client.table("tasks").select("*").eq("type", "active").execute()
            
            # Get all users info for assignee names
            users_info = {}
            for user in users_result.data:
                users_info[user["id"]] = {
                    "display_name": user.get("display_name") or user.get("email", "").split("@")[0],
                    "email": user.get("email")
                }
            
            # Process each user
            for user in users_result.data:
                user_id = user["id"]
                user_email = user.get("email")
                user_name = user.get("display_name") or user.get("email", "").split("@")[0]
                
                if not user_email:
                    continue
                
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
                project_role_map = {}  # Track user's role per project
                
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
                    continue  # Skip users with no relevant tasks
                
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
                    except (ValueError, TypeError):
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
                person_tasks_by_project = {}  # {project_id: {user_id: {name, tasks: [{title, status}]}}}
                
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
                
                self.email_service.send_daily_digest_email(
                    user_email=user_email,
                    user_name=user_name,
                    digest_data=digest_data
                )
            
            print(f"Sent daily digests to {len(users_result.data)} users")
        except Exception as e:
            print(f"Error sending daily digests: {e}")
            import traceback
            traceback.print_exc()

