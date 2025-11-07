"""Email service using SMTP (Gmail) for sending emails."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from app.config import settings

class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self):
        # Get SMTP settings from settings (which loads from .env)
        self.smtp_server = settings.smtp_server or os.getenv("SMTP_SERVER") or "smtp.gmail.com"
        self.smtp_port = settings.smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = settings.smtp_username or os.getenv("SMTP_USERNAME") or ""
        self.smtp_password = settings.smtp_password or os.getenv("SMTP_PASSWORD") or ""
        self.from_email = settings.smtp_from_email or os.getenv("SMTP_FROM_EMAIL") or self.smtp_username or ""
        self.frontend_url = settings.frontend_url
        
        if not self.smtp_username or not self.smtp_password:
            print("Warning: SMTP_USERNAME or SMTP_PASSWORD not set. Email sending will be disabled.")
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Send an email using SMTP."""
        if not self.smtp_username or not self.smtp_password:
            print(f"Email service not initialized. Would send to {to_email}: {subject}")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"Email sent successfully to {to_email}")
            return True
                
        except Exception as e:
            print(f"Error sending email to {to_email}: {e}")
            return False
    
    def send_task_assigned_email(self, user_email: str, user_name: str, task_title: str, task_id: str, project_name: str, project_id: str = None) -> bool:
        """Send email when a task is assigned to a user."""
        if project_id:
            task_url = f"{self.frontend_url}/projects/{project_id}/tasks/{task_id}"
        else:
            task_url = f"{self.frontend_url}/tasks/{task_id}"
        
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
    
    def send_mention_email(self, user_email: str, user_name: str, commenter_name: str, task_title: str, task_id: str, comment_preview: str, project_id: str = None) -> bool:
        """Send email when user is mentioned in a comment."""
        # Build proper task URL - need project_id for proper routing
        if project_id:
            task_url = f"{self.frontend_url}/projects/{project_id}/tasks/{task_id}"
        else:
            # Fallback: try to extract from task_id if it contains project info
            task_url = f"{self.frontend_url}/tasks/{task_id}"
        
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
    
    def send_task_update_email(
        self, 
        user_email: str, 
        user_name: str, 
        task_title: str, 
        task_id: str, 
        project_name: str,
        project_id: str,
        updated_by_name: str,
        update_type: str,
        update_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send email when a task is updated (status change, title, description, etc.)."""
        task_url = f"{self.frontend_url}/projects/{project_id}/tasks/{task_id}"
        
        # Determine subject and message based on update type
        update_messages = {
            "status": {
                "subject": f"Task Status Updated: {task_title}",
                "title": "Task Status Updated",
                "message": f"The status of task '{task_title}' has been changed",
                "details": update_details and f"Status changed from {update_details.get('old_status', 'N/A')} to {update_details.get('new_status', 'N/A')}"
            },
            "title": {
                "subject": f"Task Title Updated: {task_title}",
                "title": "Task Title Updated",
                "message": f"The title of task '{task_title}' has been updated",
                "details": update_details and f"New title: {update_details.get('new_title', task_title)}"
            },
            "description": {
                "subject": f"Task Description Updated: {task_title}",
                "title": "Task Description Updated",
                "message": f"The description of task '{task_title}' has been updated",
                "details": None
            },
            "priority": {
                "subject": f"Task Priority Updated: {task_title}",
                "title": "Task Priority Updated",
                "message": f"The priority of task '{task_title}' has been updated",
                "details": update_details and f"New priority: {update_details.get('new_priority', 'N/A')}"
            },
            "notes": {
                "subject": f"Task Notes Updated: {task_title}",
                "title": "Task Notes Updated",
                "message": f"The notes for task '{task_title}' have been updated",
                "details": None
            },
            "tags": {
                "subject": f"Task Tags Updated: {task_title}",
                "title": "Task Tags Updated",
                "message": f"The tags for task '{task_title}' have been updated",
                "details": update_details and f"Tags: {', '.join(update_details.get('tags', []))}"
            },
            "assignees": {
                "subject": f"Task Assignees Updated: {task_title}",
                "title": "Task Assignees Updated",
                "message": f"The assignees for task '{task_title}' have been updated",
                "details": None
            },
            "general": {
                "subject": f"Task Updated: {task_title}",
                "title": "Task Updated",
                "message": f"Task '{task_title}' has been updated",
                "details": None
            }
        }
        
        update_info = update_messages.get(update_type, update_messages["general"])
        
        subject = update_info["subject"]
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #6366F1; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
                .update-box {{ background-color: white; padding: 15px; border-left: 4px solid #6366F1; margin: 20px 0; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #6366F1; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{update_info["title"]}</h1>
                </div>
                <div class="content">
                    <p>Hi {user_name},</p>
                    <p><strong>{updated_by_name}</strong> {update_info["message"].replace(f"'{task_title}'", "this task")}.</p>
                    <div class="update-box">
                        <h2 style="margin-top: 0;">{task_title}</h2>
                        <p><strong>Project:</strong> {project_name}</p>
                        {update_info["details"] and f'<p><strong>Details:</strong> {update_info["details"]}</p>'}
                    </div>
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
        {update_info["title"]}
        
        Hi {user_name},
        
        {updated_by_name} {update_info["message"]}.
        
        Task: {task_title}
        Project: {project_name}
        {update_info["details"] and f'Details: {update_info["details"]}'}
        
        View the task: {task_url}
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_task_updates_email(
        self,
        user_email: str,
        user_name: str,
        task_title: str,
        task_id: str,
        project_name: str,
        project_id: str,
        updated_by_name: str,
        changes: List[Dict[str, Any]],
        is_new_assignment: bool = False
    ) -> bool:
        """Send email when a task is updated with multiple changes consolidated into one email."""
        task_url = f"{self.frontend_url}/projects/{project_id}/tasks/{task_id}"
        
        # Field labels for display
        field_labels = {
            "status": "Status",
            "title": "Title",
            "description": "Description",
            "priority": "Priority",
            "notes": "Notes",
            "tags": "Tags",
            "due_date": "Due Date",
            "assignees": "Assignees"
        }
        
        # Build change details
        change_items = []
        for change in changes:
            update_type = change.get("type")
            update_details = change.get("details", {})
            
            if update_type == "status":
                old_status = update_details.get("old_status", "N/A")
                new_status = update_details.get("new_status", "N/A")
                change_items.append(f"<li><strong>{field_labels.get(update_type, update_type.title())}:</strong> Changed from {old_status} to {new_status}</li>")
            elif update_type == "title":
                old_title = update_details.get("old_title", "N/A")
                new_title = update_details.get("new_title", task_title)
                change_items.append(f"<li><strong>{field_labels.get(update_type, update_type.title())}:</strong> Changed from '{old_title}' to '{new_title}'</li>")
            elif update_type == "priority":
                old_priority = update_details.get("old_priority")
                new_priority = update_details.get("new_priority", "N/A")
                if old_priority is not None:
                    change_items.append(f"<li><strong>{field_labels.get(update_type, update_type.title())}:</strong> Changed from {old_priority} to {new_priority}</li>")
                else:
                    change_items.append(f"<li><strong>{field_labels.get(update_type, update_type.title())}:</strong> Set to {new_priority}</li>")
            elif update_type == "tags":
                old_tags = update_details.get("old_tags", [])
                new_tags = update_details.get("new_tags", [])
                old_tags_str = ", ".join(old_tags) if old_tags else "None"
                new_tags_str = ", ".join(new_tags) if new_tags else "None"
                change_items.append(f"<li><strong>{field_labels.get(update_type, update_type.title())}:</strong> Changed from [{old_tags_str}] to [{new_tags_str}]</li>")
            elif update_type == "due_date":
                old_due_date = update_details.get("old_due_date", "")
                new_due_date = update_details.get("new_due_date", "N/A")
                if old_due_date:
                    change_items.append(f"<li><strong>{field_labels.get(update_type, update_type.title())}:</strong> Changed from {old_due_date} to {new_due_date}</li>")
                else:
                    change_items.append(f"<li><strong>{field_labels.get(update_type, update_type.title())}:</strong> Set to {new_due_date}</li>")
            elif update_type == "assignees":
                added = update_details.get("added", [])
                removed = update_details.get("removed", [])
                if added and removed:
                    change_items.append(f"<li><strong>{field_labels.get(update_type, update_type.title())}:</strong> Added {len(added)}, Removed {len(removed)}</li>")
                elif added:
                    change_items.append(f"<li><strong>{field_labels.get(update_type, update_type.title())}:</strong> Added {len(added)} assignee(s)</li>")
                elif removed:
                    change_items.append(f"<li><strong>{field_labels.get(update_type, update_type.title())}:</strong> Removed {len(removed)} assignee(s)</li>")
                else:
                    change_items.append(f"<li><strong>{field_labels.get(update_type, update_type.title())}:</strong> Updated</li>")
            else:
                change_items.append(f"<li><strong>{field_labels.get(update_type, update_type.title())}:</strong> Updated</li>")
        
        changes_html = "<ul style='margin: 10px 0; padding-left: 20px;'>" + "".join(change_items) + "</ul>" if change_items else "<p>No details available.</p>"
        
        # Determine subject and title
        if is_new_assignment:
            subject = f"Task Assigned: {task_title}"
            title = "Task Assigned"
            intro_message = f"You have been assigned to task '{task_title}'"
        elif len(changes) == 1:
            change_type = changes[0].get("type", "general")
            subject = f"Task {field_labels.get(change_type, change_type.title())} Updated: {task_title}"
            title = f"Task {field_labels.get(change_type, change_type.title())} Updated"
            intro_message = f"Task '{task_title}' has been updated"
        else:
            subject = f"Task Updated: {task_title}"
            title = "Task Updated"
            intro_message = f"Task '{task_title}' has been updated with {len(changes)} change(s)"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #6366F1; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
                .update-box {{ background-color: white; padding: 15px; border-left: 4px solid #6366F1; margin: 20px 0; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #6366F1; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .changes-list {{ margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                </div>
                <div class="content">
                    <p>Hi {user_name},</p>
                    <p><strong>{updated_by_name}</strong> {intro_message}.</p>
                    <div class="update-box">
                        <h2 style="margin-top: 0;">{task_title}</h2>
                        <p><strong>Project:</strong> {project_name}</p>
                        <div class="changes-list">
                            <p><strong>Changes:</strong></p>
                            {changes_html}
                        </div>
                    </div>
                    <a href="{task_url}" class="button">View Task</a>
                </div>
                <div class="footer">
                    <p>This is an automated notification from SPM.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Build text version
        change_items_text = []
        for change in changes:
            update_type = change.get("type")
            update_details = change.get("details", {})
            
            if update_type == "status":
                old_status = update_details.get("old_status", "N/A")
                new_status = update_details.get("new_status", "N/A")
                change_items_text.append(f"- {field_labels.get(update_type, update_type.title())}: Changed from {old_status} to {new_status}")
            elif update_type == "title":
                old_title = update_details.get("old_title", "N/A")
                new_title = update_details.get("new_title", task_title)
                change_items_text.append(f"- {field_labels.get(update_type, update_type.title())}: Changed from '{old_title}' to '{new_title}'")
            elif update_type == "priority":
                old_priority = update_details.get("old_priority")
                new_priority = update_details.get("new_priority", "N/A")
                if old_priority is not None:
                    change_items_text.append(f"- {field_labels.get(update_type, update_type.title())}: Changed from {old_priority} to {new_priority}")
                else:
                    change_items_text.append(f"- {field_labels.get(update_type, update_type.title())}: Set to {new_priority}")
            elif update_type == "tags":
                old_tags = update_details.get("old_tags", [])
                new_tags = update_details.get("new_tags", [])
                old_tags_str = ", ".join(old_tags) if old_tags else "None"
                new_tags_str = ", ".join(new_tags) if new_tags else "None"
                change_items_text.append(f"- {field_labels.get(update_type, update_type.title())}: Changed from [{old_tags_str}] to [{new_tags_str}]")
            elif update_type == "due_date":
                old_due_date = update_details.get("old_due_date", "")
                new_due_date = update_details.get("new_due_date", "N/A")
                if old_due_date:
                    change_items_text.append(f"- {field_labels.get(update_type, update_type.title())}: Changed from {old_due_date} to {new_due_date}")
                else:
                    change_items_text.append(f"- {field_labels.get(update_type, update_type.title())}: Set to {new_due_date}")
            elif update_type == "assignees":
                added = update_details.get("added", [])
                removed = update_details.get("removed", [])
                if added and removed:
                    change_items_text.append(f"- {field_labels.get(update_type, update_type.title())}: Added {len(added)}, Removed {len(removed)}")
                elif added:
                    change_items_text.append(f"- {field_labels.get(update_type, update_type.title())}: Added {len(added)} assignee(s)")
                elif removed:
                    change_items_text.append(f"- {field_labels.get(update_type, update_type.title())}: Removed {len(removed)} assignee(s)")
                else:
                    change_items_text.append(f"- {field_labels.get(update_type, update_type.title())}: Updated")
            else:
                change_items_text.append(f"- {field_labels.get(update_type, update_type.title())}: Updated")
        
        changes_text = "\n".join(change_items_text) if change_items_text else "No details available."
        
        text_content = f"""
        {title}
        
        Hi {user_name},
        
        {updated_by_name} {intro_message}.
        
        Task: {task_title}
        Project: {project_name}
        
        Changes:
        {changes_text}
        
        View the task: {task_url}
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_daily_digest_email(self, user_email: str, user_name: str, digest_data: Dict[str, Any]) -> bool:
        """Send daily digest email with comprehensive task information."""
        is_manager = digest_data.get("is_manager", False)
        role_text = "Manager" if is_manager else "Employee"
        subject = f"Daily Task Digest - SPM ({role_text})"
        
        # Extract data
        tasks_due_soon = digest_data.get("tasks_due_soon", [])
        overdue_tasks = digest_data.get("overdue_tasks", [])
        overdue_percentage = digest_data.get("overdue_percentage", 0)
        status_summary = digest_data.get("status_summary", {})
        completion_percentage = digest_data.get("completion_percentage", 0)
        total_tasks = digest_data.get("total_tasks", 0)
        person_tasks_by_project = digest_data.get("person_tasks_by_project", {})
        projects = digest_data.get("projects", {})
        
        # Build tasks due soon HTML
        tasks_html = ""
        if tasks_due_soon:
            for task in tasks_due_soon:
                project_name = projects.get(task.get("project_id", ""), "Unknown Project")
                status_color = {
                    "todo": "#94A3B8",
                    "in_progress": "#3B82F6",
                    "completed": "#10B981",
                    "blocked": "#EF4444"
                }.get(task.get("status", "todo"), "#94A3B8")
                tasks_html += f"""
                <div style="padding: 12px; margin: 8px 0; background-color: white; border-left: 4px solid #F59E0B; border-radius: 4px;">
                    <strong>{task.get("title", "Untitled")}</strong><br>
                    <span style="color: #666; font-size: 13px;">Project: {project_name} | Due: {task.get("due_date", "N/A")} | Status: <span style="color: {status_color}; font-weight: bold;">{task.get("status", "todo").upper()}</span></span>
                </div>
                """
        else:
            tasks_html = "<p style='color: #666; padding: 10px;'>No tasks due in the next 48 hours.</p>"
        
        # Build overdue tasks HTML
        overdue_html = ""
        if overdue_tasks:
            for task in overdue_tasks:
                project_name = projects.get(task.get("project_id", ""), "Unknown Project")
                status_color = {
                    "todo": "#94A3B8",
                    "in_progress": "#3B82F6",
                    "completed": "#10B981",
                    "blocked": "#EF4444"
                }.get(task.get("status", "todo"), "#94A3B8")
                overdue_html += f"""
                <div style="padding: 12px; margin: 8px 0; background-color: white; border-left: 4px solid #EF4444; border-radius: 4px;">
                    <strong>{task.get("title", "Untitled")}</strong><br>
                    <span style="color: #666; font-size: 13px;">Project: {project_name} | Due: {task.get("due_date", "N/A")} | Status: <span style="color: {status_color}; font-weight: bold;">{task.get("status", "todo").upper()}</span></span>
                </div>
                """
        else:
            overdue_html = "<p style='color: #666; padding: 10px;'>No overdue tasks.</p>"
        
        # Build status summary HTML
        status_html = f"""
        <div style="background-color: white; padding: 15px; border-radius: 4px; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px; flex-wrap: wrap;">
                <span><strong>Total Tasks:</strong> {total_tasks}</span>
                <span><strong>Completion:</strong> <span style="color: #10B981; font-weight: bold;">{completion_percentage}%</span></span>
                <span><strong>Overdue:</strong> <span style="color: #EF4444; font-weight: bold;">{overdue_percentage}%</span></span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
                <div style="padding: 8px; background-color: #F1F5F9; border-radius: 4px;">
                    <strong style="color: #94A3B8;">To Do:</strong> {status_summary.get("todo", 0)}
                </div>
                <div style="padding: 8px; background-color: #EFF6FF; border-radius: 4px;">
                    <strong style="color: #3B82F6;">In Progress:</strong> {status_summary.get("in_progress", 0)}
                </div>
                <div style="padding: 8px; background-color: #D1FAE5; border-radius: 4px;">
                    <strong style="color: #10B981;">Completed:</strong> {status_summary.get("completed", 0)}
                </div>
                <div style="padding: 8px; background-color: #FEE2E2; border-radius: 4px;">
                    <strong style="color: #EF4444;">Blocked:</strong> {status_summary.get("blocked", 0)}
                </div>
            </div>
        </div>
        """
        
        # Build per-person task breakdown HTML
        person_breakdown_html = ""
        if person_tasks_by_project:
            for project_id, people in person_tasks_by_project.items():
                project_name = projects.get(project_id, "Unassigned Project")
                person_breakdown_html += f"""
                <div style="margin: 15px 0; padding: 15px; background-color: white; border-radius: 4px; border-left: 4px solid #4F46E5;">
                    <h3 style="margin: 0 0 15px 0; color: #4F46E5; font-size: 16px;">{project_name}</h3>
                """
                
                for user_id, person_data in people.items():
                    person_name = person_data.get("name", "Unknown")
                    person_tasks = person_data.get("tasks", [])
                    task_count = len(person_tasks)
                    
                    person_breakdown_html += f"""
                    <div style="margin: 10px 0; padding: 10px; background-color: #F9FAFB; border-radius: 4px;">
                        <strong>{person_name}</strong> ({task_count} task{'s' if task_count != 1 else ''}):
                        <ul style="margin: 8px 0 0 0; padding-left: 20px;">
                    """
                    
                    for task in person_tasks:
                        status_color = {
                            "todo": "#94A3B8",
                            "in_progress": "#3B82F6",
                            "completed": "#10B981",
                            "blocked": "#EF4444"
                        }.get(task.get("status", "todo"), "#94A3B8")
                        person_breakdown_html += f"""
                            <li style="margin: 4px 0;">
                                {task.get("title", "Untitled")} - 
                                <span style="color: {status_color}; font-weight: bold;">{task.get("status", "todo").upper()}</span>
                            </li>
                        """
                    
                    person_breakdown_html += """
                        </ul>
                    </div>
                    """
                
                person_breakdown_html += "</div>"
        else:
            person_breakdown_html = "<p style='color: #666; padding: 10px;'>No task assignments found.</p>"
        
        # Build HTML email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
                .section {{ margin: 25px 0; }}
                .section-title {{ font-size: 18px; font-weight: bold; margin-bottom: 12px; color: #4F46E5; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">Daily Task Digest</h1>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">{role_text} Summary</p>
                </div>
                <div class="content">
                    <p style="font-size: 16px;">Hi <strong>{user_name}</strong>,</p>
                    <p>Here's your daily summary of tasks and updates:</p>
                    
                    <div class="section">
                        <div class="section-title">📊 Status Summary</div>
                        {status_html}
                    </div>
                    
                    <div class="section">
                        <div class="section-title">🚨 Overdue Tasks</div>
                        {overdue_html}
                    </div>
                    
                    <div class="section">
                        <div class="section-title">⏰ Tasks Due in Next 48 Hours</div>
                        {tasks_html}
                    </div>
                    
                    <div class="section">
                        <div class="section-title">👥 Task Breakdown by Person & Project</div>
                        {person_breakdown_html}
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #E5E7EB; text-align: center; color: #666; font-size: 12px;">
                        <p>This is an automated notification from SPM.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Build text content
        text_content = f"""Daily Task Digest ({role_text})
        
Hi {user_name},

Status Summary:
- Total Tasks: {total_tasks}
- Completion: {completion_percentage}%
- Overdue: {overdue_percentage}%
- To Do: {status_summary.get("todo", 0)}
- In Progress: {status_summary.get("in_progress", 0)}
- Completed: {status_summary.get("completed", 0)}
- Blocked: {status_summary.get("blocked", 0)}

Overdue Tasks:
{chr(10).join([f"- {t.get('title')} (Project: {projects.get(t.get('project_id', ''), 'Unknown')}, Due: {t.get('due_date', 'N/A')}, Status: {t.get('status')})" for t in overdue_tasks]) if overdue_tasks else "No overdue tasks."}

Tasks Due in Next 48 Hours:
{chr(10).join([f"- {t.get('title')} (Project: {projects.get(t.get('project_id', ''), 'Unknown')}, Due: {t.get('due_date', 'N/A')}, Status: {t.get('status')})" for t in tasks_due_soon]) if tasks_due_soon else "No tasks due in the next 48 hours."}

Task Breakdown by Person & Project:
"""
        
        for project_id, people in person_tasks_by_project.items():
            project_name = projects.get(project_id, "Unassigned Project")
            text_content += f"\n{project_name}:\n"
            for user_id, person_data in people.items():
                person_name = person_data.get("name", "Unknown")
                person_tasks = person_data.get("tasks", [])
                text_content += f"  {person_name} ({len(person_tasks)} tasks):\n"
                for task in person_tasks:
                    text_content += f"    - {task.get('title')} [{task.get('status', 'todo').upper()}]\n"
        
        text_content += "\nThis is an automated notification from SPM."
        
        return self.send_email(user_email, subject, html_content, text_content)
