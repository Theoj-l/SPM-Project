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
        import asyncio
        
        # Check deadline reminders every hour
        self.scheduler.add_job(
            lambda: asyncio.run(self.check_deadline_reminders()),
            trigger=CronTrigger(minute=0),  # Run at the top of every hour
            id="deadline_reminders",
            replace_existing=True
        )
        
        # Check overdue tasks every hour
        self.scheduler.add_job(
            lambda: asyncio.run(self.check_overdue_tasks()),
            trigger=CronTrigger(minute=0),  # Run at the top of every hour
            id="overdue_tasks",
            replace_existing=True
        )
        
        # Send daily digests at 6 PM SGT (10 AM UTC)
        self.scheduler.add_job(
            lambda: asyncio.run(self.send_daily_digests()),
            trigger=CronTrigger(hour=10, minute=0),  # 6 PM SGT = 10 AM UTC
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
                assignee_ids = task.get("assigned", [])
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
                assignee_ids = task.get("assigned", [])
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
        """Send daily digest emails to managers and admins."""
        try:
            # Get all users with manager or admin roles
            result = self.client.table("users").select("id, email, display_name, roles").execute()
            
            managers_and_admins = []
            for user in result.data:
                roles = user.get("roles", [])
                if isinstance(roles, str):
                    roles = [r.strip() for r in roles.split(",")]
                
                if "manager" in roles or "admin" in roles or "hr" in [r.lower() for r in roles]:
                    managers_and_admins.append(user)
            
            now = datetime.utcnow()
            tomorrow = now + timedelta(days=2)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get all projects for mapping
            projects_result = self.client.table("projects").select("id, name").execute()
            projects_map = {p["id"]: p["name"] for p in projects_result.data}
            
            # Get tasks due in next 48 hours
            tasks_result = self.client.table("tasks").select("*").eq("type", "active").in_("status", ["todo", "in_progress", "blocked"]).execute()
            
            tasks_due_soon = []
            for task in tasks_result.data:
                if not task.get("due_date"):
                    continue
                
                try:
                    due_date = datetime.strptime(task["due_date"][:10], "%Y-%m-%d")
                    if today_start <= due_date <= tomorrow:
                        tasks_due_soon.append({
                            "id": task.get("id"),
                            "title": task.get("title"),
                            "due_date": task["due_date"][:10],
                            "project_id": task.get("project_id"),
                            "status": task.get("status")
                        })
                except (ValueError, TypeError):
                    continue
            
            # Get recent status changes (last 24 hours)
            # Note: This is a simplified version. In production, you'd track status changes in a separate table
            status_changes = []  # Can be enhanced to track actual status changes
            
            # Send digest to each manager/admin
            for user in managers_and_admins:
                user_email = user.get("email")
                user_name = user.get("display_name") or user.get("email", "").split("@")[0]
                
                # Filter tasks by projects the user has access to (simplified - send all)
                digest_data = {
                    "tasks_due_soon": tasks_due_soon,
                    "status_changes": status_changes,
                    "projects": projects_map
                }
                
                self.email_service.send_daily_digest_email(
                    user_email=user_email,
                    user_name=user_name,
                    digest_data=digest_data
                )
            
            print(f"Sent daily digests to {len(managers_and_admins)} managers/admins")
        except Exception as e:
            print(f"Error sending daily digests: {e}")

