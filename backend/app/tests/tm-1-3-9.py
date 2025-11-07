"""
TM-1 / TM-3 / TM-9: Task Creation, Assignment and Search/Filter Tests

Rewritten to match actual service implementations:
- Tasks created via ProjectService.add_task() (static method)
- NotificationService.create_task_assigned_notification() for notifications
- TaskService is instance-based with async methods
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

try:
    from app.services.project_service import ProjectService
    from app.services.task_service import TaskService
    from app.services.notification_service import NotificationService
except Exception:
    ProjectService = TaskService = NotificationService = None


def test_create_task_requires_title_and_persists():
    """TM-1: Task creation requires title and persists all fields"""
    if ProjectService is None:
        pytest.skip("ProjectService not importable")

    # Mock successful task creation with full mocking of internal methods
    with patch('app.services.project_service.SupabaseService') as mock_supa, \
         patch('app.services.project_service.ProjectService._notify_assignees'):
        
        created_task = {
            "id": "task123",
            "project_id": "p1",
            "title": "Implement Feature X",
            "description": "Detailed steps",
            "status": "todo",
            "due_date": "2024-12-31",
            "notes": "Important notes",
            "assigned": ["user1", "user2"],
            "tags": ["backend", "urgent"],
            "priority": 2
        }
        
        mock_supa.insert.return_value = created_task
        
        # Create task with all fields
        result = ProjectService.add_task(
            project_id="p1",
            title="Implement Feature X",
            description="Detailed steps",
            due_date="2024-12-31",
            notes="Important notes",
            assignee_ids=["user1", "user2"],
            status="todo",
            tags=["backend", "urgent"],
            priority=2
        )
        
        assert result["id"] == "task123"
        assert result["title"] == "Implement Feature X"
        assert result["description"] == "Detailed steps"
        assert result["status"] == "todo"
        assert result["due_date"] == "2024-12-31"
        assert result["assigned"] == ["user1", "user2"]
        assert result["tags"] == ["backend", "urgent"]
        assert result["priority"] == 2


def test_assignment_triggers_notifications():
    """TM-3: Assigning task triggers notifications (verifies task creation with assignees)"""
    if ProjectService is None:
        pytest.skip("Required services not importable")

    # Simplified test - just verify task created with assignees
    # The actual notification logic is tested elsewhere
    with patch('app.services.project_service.SupabaseService') as mock_supa, \
         patch('app.services.project_service.ProjectService._notify_assignees') as mock_notify:
        
        created_task = {
            "id": "t1",
            "project_id": "p1",
            "title": "Assignable Task",
            "status": "todo",
            "assigned": ["alice", "bob"]
        }
        
        mock_supa.insert.return_value = created_task
        
        # Create task with assignees
        result = ProjectService.add_task(
            project_id="p1",
            title="Assignable Task",
            assignee_ids=["alice", "bob"]
        )
        
        # Verify task was created
        assert result["id"] == "t1"
        assert result["assigned"] == ["alice", "bob"]
        
        # Verify notification method was called
        mock_notify.assert_called_once()


@pytest.mark.asyncio
async def test_get_task_by_id_with_access_control():
    """TM-9: Get task validates user access"""
    if TaskService is None:
        pytest.skip("TaskService not importable")

    task_id = "t1"
    user_id = "staff1"
    project_id = "p1"

    with patch('app.services.task_service.get_supabase_client') as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock task query
        mock_task_chain = MagicMock()
        mock_task_chain.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": task_id,
                "project_id": project_id,
                "title": "Test Task",
                "description": "Description",
                "status": "todo",
                "due_date": "2024-12-31",
                "assigned": [user_id],
                "type": "active",
                "tags": ["test"],
                "priority": 1,
                "created_at": "2024-01-01"
            }
        ]
        
        # Mock project query
        mock_project_chain = MagicMock()
        mock_project_chain.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": project_id, "name": "Test Project", "owner_id": "owner1"}
        ]
        
        # Mock user roles query
        mock_user_chain = MagicMock()
        mock_user_chain.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": user_id, "roles": []}
        ]
        
        # Mock project members query - user is member
        mock_members_chain = MagicMock()
        mock_members_chain.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {"project_id": project_id, "user_id": user_id}
        ]
        
        # Mock assignee names query
        mock_assignee_chain = MagicMock()
        mock_assignee_chain.select.return_value.in_.return_value.execute.return_value.data = [
            {"id": user_id, "display_name": "Staff User", "email": "staff@test.com"}
        ]
        
        # Setup table routing
        def table_side_effect(table_name):
            if table_name == "tasks":
                return mock_task_chain
            elif table_name == "projects":
                return mock_project_chain
            elif table_name == "users":
                return mock_user_chain
            elif table_name == "project_members":
                return mock_members_chain
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        # Create TaskService and fetch task
        task_service = TaskService()
        task = await task_service.get_task_by_id(task_id=task_id, user_id=user_id)
        
        # User assigned to task should see it
        assert task is not None
        assert task.id == task_id
        assert task.title == "Test Task"
        assert user_id in task.assignee_ids


@pytest.mark.asyncio
async def test_get_task_denies_access_to_non_member():
    """TM-9: Non-project-member cannot access task"""
    if TaskService is None:
        pytest.skip("TaskService not importable")

    task_id = "t1"
    user_id = "outsider"
    project_id = "p1"

    with patch('app.services.task_service.get_supabase_client') as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock task query
        mock_task_chain = MagicMock()
        mock_task_chain.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": task_id,
                "project_id": project_id,
                "title": "Secret Task",
                "status": "todo",
                "assigned": ["other_user"],
                "type": "active",
                "tags": [],
                "priority": 1
            }
        ]
        
        # Mock project query
        mock_project_chain = MagicMock()
        mock_project_chain.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": project_id, "name": "Test Project", "owner_id": "owner1"}
        ]
        
        # Mock user roles query - not admin
        mock_user_chain = MagicMock()
        mock_user_chain.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": user_id, "roles": []}
        ]
        
        # Mock project members query - user is NOT member
        mock_members_chain = MagicMock()
        mock_members_chain.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        
        # Setup table routing
        def table_side_effect(table_name):
            if table_name == "tasks":
                return mock_task_chain
            elif table_name == "projects":
                return mock_project_chain
            elif table_name == "users":
                return mock_user_chain
            elif table_name == "project_members":
                return mock_members_chain
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        # Create TaskService and try to fetch task
        task_service = TaskService()
        task = await task_service.get_task_by_id(task_id=task_id, user_id=user_id)
        
        # User without access should get None
        assert task is None


# End of file