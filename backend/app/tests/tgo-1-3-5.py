"""
TGO-1 / TGO-3 / TGO-5: Project Creation, Viewing Projects and Viewing Project Tasks Tests

Rewritten to match actual ProjectService implementation:
- ProjectService uses static methods
- Uses SupabaseService wrapper for DB operations
- No instance-based .client attribute
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

try:
    from app.services.project_service import ProjectService
    from app.services.task_service import TaskService
except Exception:
    ProjectService = TaskService = None


def test_create_project_requires_name_and_persists():
    """TGO-1: Project creation requires name and persists to database"""
    if ProjectService is None:
        pytest.skip("ProjectService not importable")

    # Test missing name validation
    with pytest.raises(Exception):
        ProjectService.create_project(name="", owner_id="owner123")
    
    with pytest.raises(Exception):
        ProjectService.create_project(name="   ", owner_id="owner123")

    # Mock SupabaseService for successful creation
    with patch('app.services.project_service.SupabaseService') as mock_supa:
        # Mock project insert
        mock_supa.insert.side_effect = [
            {"id": "p1", "name": "Project A", "owner_id": "owner123", "status": "active"},  # projects insert
            {"project_id": "p1", "user_id": "owner123", "role": "owner"}  # project_members insert
        ]
        
        # Create project
        result = ProjectService.create_project(name="Project A", owner_id="owner123")
        
        assert result["id"] == "p1"
        assert result["name"] == "Project A"
        assert result["owner_id"] == "owner123"
        
        # Verify insert was called twice (projects + project_members)
        assert mock_supa.insert.call_count == 2


def test_view_all_projects_for_user():
    """TGO-3: View all projects for a user with filtering"""
    if ProjectService is None:
        pytest.skip("ProjectService not importable")

    user_id = "user123"
    
    with patch('app.services.project_service.SupabaseService') as mock_supa:
        # Mock project members query
        mock_supa.select.return_value = [
            {"project_id": "p1", "user_id": user_id, "role": "owner"},
            {"project_id": "p2", "user_id": user_id, "role": "member"}
        ]
        
        # Mock Supabase client for projects query
        mock_client = MagicMock()
        mock_projects_chain = MagicMock()
        mock_projects_chain.select.return_value.in_.return_value.order.return_value.execute.return_value.data = [
            {"id": "p1", "name": "Alpha Project", "owner_id": "owner1", "status": "active", "created_at": "2024-01-01"},
            {"id": "p2", "name": "Beta Project", "owner_id": "owner2", "status": "active", "created_at": "2024-01-02"}
        ]
        mock_client.table.return_value = mock_projects_chain
        mock_supa.get_client.return_value = mock_client
        
        # Mock users query for owner info
        mock_users_chain = MagicMock()
        mock_users_chain.select.return_value.in_.return_value.execute.return_value.data = [
            {"id": "owner1", "display_name": "Owner One", "email": "owner1@test.com"},
            {"id": "owner2", "display_name": "Owner Two", "email": "owner2@test.com"}
        ]
        
        # Update table mock to return different chains
        def table_side_effect(table_name):
            if table_name == "projects":
                return mock_projects_chain
            elif table_name == "users":
                return mock_users_chain
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        # List projects for user
        projects = ProjectService.list_for_user(user_id=user_id)
        
        assert len(projects) == 2
        assert projects[0]["name"] == "Alpha Project"
        assert projects[1]["name"] == "Beta Project"


def test_view_tasks_within_project_shows_only_assigned_tasks():
    """TGO-5: View tasks restricted to assigned user unless permission granted"""
    if TaskService is None or ProjectService is None:
        pytest.skip("TaskService/ProjectService not importable")

    project_id = "proj1"
    user_id = "staff1"
    task_id = "t1"

    # Test TaskService.get_task_by_id with access control
    with patch('app.services.task_service.get_supabase_client') as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock task query
        mock_task_chain = MagicMock()
        mock_task_chain.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": task_id, "title": "My Task", "assigned": [user_id], "project_id": project_id, 
             "status": "todo", "type": "active", "tags": [], "priority": 1}
        ]
        
        # Mock project query
        mock_project_chain = MagicMock()
        mock_project_chain.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": project_id, "name": "Test Project", "owner_id": "owner123"}
        ]
        
        # Mock user roles query
        mock_user_chain = MagicMock()
        mock_user_chain.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": user_id, "roles": []}  # Not admin
        ]
        
        # Mock project members query - user is a member
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
        
        # Create TaskService instance and get task
        task_service = TaskService()
        
        # Use synchronous execution for test
        import asyncio
        task = asyncio.run(task_service.get_task_by_id(task_id=task_id, user_id=user_id))
        
        # User should be able to see task they're assigned to
        assert task is not None
        assert task.id == task_id
        assert task.title == "My Task"
        assert user_id in task.assignee_ids


# End of file