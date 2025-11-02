"""Email service using Resend for sending emails."""

import os
from typing import List, Optional, Dict, Any
import resend
from app.config import settings

class EmailService:
    """Service for sending emails via Resend."""
    
    def __init__(self):
        # Get API key from settings (which loads from .env)
        self.api_key = settings.resend_api_key or os.getenv("RESEND_API_KEY") or ""
        # Use Resend's default sending email if no custom email provided
        # Options: onboarding@resend.dev (for testing) or delivered@resend.dev
        self.from_email = settings.resend_from_email or os.getenv("RESEND_FROM_EMAIL") or os.getenv("FROM_EMAIL") or "onboarding@resend.dev"
        self.frontend_url = settings.frontend_url
        
        if self.api_key:
            try:
                resend.api_key = self.api_key
            except Exception as e:
                print(f"Warning: Failed to initialize Resend API key: {e}")
        else:
            print("Warning: RESEND_API_KEY not set. Email sending will be disabled.")
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Send an email using Resend."""
        if not self.api_key:
            print(f"Email service not initialized. Would send to {to_email}: {subject}")
            return False
        
        try:
            params = {
                "from": self.from_email,
                "to": to_email,
                "subject": subject,
                "html": html_content,
            }
            
            if text_content:
                params["text"] = text_content
            
            response = resend.Emails.send(params)
            
            if response and hasattr(response, 'id'):
                print(f"Email sent successfully to {to_email}, id: {response.id}")
                return True
            elif response and hasattr(response, 'error'):
                print(f"Failed to send email to {to_email}: {response.error}")
                return False
            else:
                print(f"Email sent successfully to {to_email}")
                return True
                
        except Exception as e:
            print(f"Error sending email to {to_email}: {e}")
            return False
    
    def send_task_assigned_email(self, user_email: str, user_name: str, task_title: str, task_id: str, project_name: str) -> bool:
        """Send email when a task is assigned to a user."""
        task_url = f"{self.frontend_url}/projects/{task_id.split('-')[0]}/tasks/{task_id}" if '-' in task_id else f"{self.frontend_url}/tasks/{task_id}"
        
        subject = f"New Task Assigned: {task_title}"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Task Assigned</h1>
                </div>
                <div class="content">
                    <p>Hi {user_name},</p>
                    <p>You have been assigned to a new task:</p>
                    <h2>{task_title}</h2>
                    <p><strong>Project:</strong> {project_name}</p>
                    <a href="{task_url}" class="button">View Task</a>
                </div>
                <div class="footer">
                    <p>This is an automated notification from SPM.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        New Task Assigned
        
        Hi {user_name},
        
        You have been assigned to a new task: {task_title}
        Project: {project_name}
        
        View the task: {task_url}
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_deadline_reminder_email(self, user_email: str, user_name: str, task_title: str, task_id: str, project_name: str, hours_remaining: int) -> bool:
        """Send email reminder when deadline is approaching (24 hours)."""
        task_url = f"{self.frontend_url}/projects/{task_id.split('-')[0]}/tasks/{task_id}" if '-' in task_id else f"{self.frontend_url}/tasks/{task_id}"
        
        subject = f"Deadline Reminder: {task_title}"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #F59E0B; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #F59E0B; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Deadline Reminder</h1>
                </div>
                <div class="content">
                    <p>Hi {user_name},</p>
                    <p>This is a reminder that your task deadline is approaching:</p>
                    <h2>{task_title}</h2>
                    <p><strong>Project:</strong> {project_name}</p>
                    <p><strong>Time remaining:</strong> {hours_remaining} hours</p>
                    <a href="{task_url}" class="button">View Task</a>
                </div>
                <div class="footer">
                    <p>This is an automated notification from SPM.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Deadline Reminder
        
        Hi {user_name},
        
        This is a reminder that your task deadline is approaching:
        Task: {task_title}
        Project: {project_name}
        Time remaining: {hours_remaining} hours
        
        View the task: {task_url}
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_overdue_email(self, user_email: str, user_name: str, task_title: str, task_id: str, project_name: str) -> bool:
        """Send email when a task is overdue (24 hours past deadline)."""
        task_url = f"{self.frontend_url}/projects/{task_id.split('-')[0]}/tasks/{task_id}" if '-' in task_id else f"{self.frontend_url}/tasks/{task_id}"
        
        subject = f"Task Overdue: {task_title}"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #EF4444; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #EF4444; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Task Overdue</h1>
                </div>
                <div class="content">
                    <p>Hi {user_name},</p>
                    <p>This task is now overdue:</p>
                    <h2>{task_title}</h2>
                    <p><strong>Project:</strong> {project_name}</p>
                    <a href="{task_url}" class="button">View Task</a>
                </div>
                <div class="footer">
                    <p>This is an automated notification from SPM.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Task Overdue
        
        Hi {user_name},
        
        This task is now overdue:
        Task: {task_title}
        Project: {project_name}
        
        View the task: {task_url}
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_mention_email(self, user_email: str, user_name: str, commenter_name: str, task_title: str, task_id: str, comment_preview: str) -> bool:
        """Send email when user is mentioned in a comment."""
        task_url = f"{self.frontend_url}/projects/{task_id.split('-')[0]}/tasks/{task_id}" if '-' in task_id else f"{self.frontend_url}/tasks/{task_id}"
        
        subject = f"You were mentioned in a comment on: {task_title}"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #8B5CF6; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
                .comment-box {{ background-color: white; padding: 15px; border-left: 4px solid #8B5CF6; margin: 20px 0; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #8B5CF6; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>You Were Mentioned</h1>
                </div>
                <div class="content">
                    <p>Hi {user_name},</p>
                    <p><strong>{commenter_name}</strong> mentioned you in a comment on task:</p>
                    <h2>{task_title}</h2>
                    <div class="comment-box">
                        <p>{comment_preview}</p>
                    </div>
                    <a href="{task_url}" class="button">View Comment</a>
                </div>
                <div class="footer">
                    <p>This is an automated notification from SPM.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        You Were Mentioned
        
        Hi {user_name},
        
        {commenter_name} mentioned you in a comment on task: {task_title}
        
        Comment: {comment_preview}
        
        View the comment: {task_url}
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_daily_digest_email(self, user_email: str, user_name: str, digest_data: Dict[str, Any]) -> bool:
        """Send daily digest email to managers/HR/Admin."""
        subject = "Daily Task Digest - SPM"
        
        # Build digest content
        tasks_due_soon = digest_data.get("tasks_due_soon", [])
        status_changes = digest_data.get("status_changes", [])
        projects = digest_data.get("projects", {})
        
        tasks_html = ""
        if tasks_due_soon:
            for task in tasks_due_soon:
                project_name = projects.get(task.get("project_id", ""), "Unknown Project")
                tasks_html += f"""
                <div style="padding: 10px; margin: 10px 0; background-color: white; border-left: 4px solid #F59E0B;">
                    <strong>{task.get("title", "Untitled")}</strong><br>
                    <span style="color: #666; font-size: 14px;">Project: {project_name} | Due: {task.get("due_date", "N/A")}</span>
                </div>
                """
        else:
            tasks_html = "<p style='color: #666;'>No tasks due in the next 48 hours.</p>"
        
        changes_html = ""
        if status_changes:
            for change in status_changes:
                project_name = projects.get(change.get("project_id", ""), "Unknown Project")
                changes_html += f"""
                <div style="padding: 10px; margin: 10px 0; background-color: white; border-left: 4px solid #4F46E5;">
                    <strong>{change.get("task_title", "Untitled")}</strong> - Status changed to <strong>{change.get("status", "Unknown")}</strong><br>
                    <span style="color: #666; font-size: 14px;">Project: {project_name}</span>
                </div>
                """
        else:
            changes_html = "<p style='color: #666;'>No status changes today.</p>"
        
        if not tasks_due_soon and not status_changes:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Daily Digest</h1>
                    </div>
                    <div class="content">
                        <p>Hi {user_name},</p>
                        <p>No new tasks or status changes today.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
                    .section {{ margin: 20px 0; }}
                    .section-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #4F46E5; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Daily Task Digest</h1>
                    </div>
                    <div class="content">
                        <p>Hi {user_name},</p>
                        <p>Here's your daily summary of tasks and updates:</p>
                        
                        <div class="section">
                            <div class="section-title">Tasks Due in Next 48 Hours</div>
                            {tasks_html}
                        </div>
                        
                        <div class="section">
                            <div class="section-title">Recent Status Changes</div>
                            {changes_html}
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
        
        text_content = f"""
        Daily Task Digest
        
        Hi {user_name},
        
        Tasks Due in Next 48 Hours:
        {chr(10).join([f"- {t.get('title')} (Project: {projects.get(t.get('project_id', ''), 'Unknown')}, Due: {t.get('due_date', 'N/A')})" for t in tasks_due_soon]) if tasks_due_soon else "No tasks due in the next 48 hours."}
        
        Recent Status Changes:
        {chr(10).join([f"- {c.get('task_title')} - Status: {c.get('status')} (Project: {projects.get(c.get('project_id', ''), 'Unknown')})" for c in status_changes]) if status_changes else "No status changes today."}
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
