"""Test email router for testing email functionality."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.email_service import EmailService

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
        
        if not email_service.api_key:
            raise HTTPException(
                status_code=500,
                detail="RESEND_API_KEY not configured. Please set it in your .env file."
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
            digest_data = {
                "tasks_due_soon": [
                    {"id": "task-1", "title": "Complete Q1 Report", "due_date": "2024-12-25", "project_id": "proj-1", "status": "in_progress"},
                    {"id": "task-2", "title": "Review Budget Proposal", "due_date": "2024-12-26", "project_id": "proj-2", "status": "todo"},
                ],
                "status_changes": [
                    {"task_title": "Update Website", "status": "completed", "project_id": "proj-1"},
                    {"task_title": "Client Meeting", "status": "in_progress", "project_id": "proj-2"},
                ],
                "projects": {
                    "proj-1": "Project Alpha",
                    "proj-2": "Project Beta"
                }
            }
            success = email_service.send_daily_digest_email(
                user_email=request.to_email,
                user_name="Test Manager",
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

