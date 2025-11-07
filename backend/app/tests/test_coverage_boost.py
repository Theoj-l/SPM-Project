"""
Coverage Boost Tests

These tests target untested or low-coverage areas to push overall coverage to 80%+.
Focus areas:
- Services (notification, user, team) - currently 16-25% coverage
- Project service additional methods - currently 23% coverage
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from datetime import datetime, timedelta
import uuid


# ============================================================================
# Notification Service Tests (currently 25% coverage)
# ============================================================================

def test_notification_service_create_notification():
    """Test creating a notification"""
    from app.services.notification_service import NotificationService
    from app.models.notification import NotificationCreate
    
    service = NotificationService()
    
    with patch.object(service.client, 'table') as mock_table:
        mock_chain = MagicMock()
        mock_chain.insert.return_value.execute.return_value.data = [{
            "id": "notif1",
            "user_id": "user1",
            "type": "task_assigned",
            "title": "New Task Assigned",
            "message": "You have been assigned to a task",
            "read": False
        }]
        mock_table.return_value = mock_chain
        
        notification_data = NotificationCreate(
            user_id="user1",
            type="task_assigned",
            title="New Task Assigned",
            message="You have been assigned to a task"
        )
        
        result = service.create_notification(notification_data)
        
        assert result is not None
        assert result.read == False


def test_notification_service_create_task_assigned_notification():
    """Test creating task assignment notification"""
    from app.services.notification_service import NotificationService
    
    service = NotificationService()
    
    with patch.object(service.client, 'table') as mock_table:
        mock_chain = MagicMock()
        mock_chain.insert.return_value.execute.return_value.data = [{
            "id": "notif1",
            "user_id": "assignee1",
            "type": "task_assigned",
            "title": "New Task Assigned",
            "message": "You have been assigned to task 'Test Task'"
        }]
        mock_table.return_value = mock_chain
        
        result = service.create_task_assigned_notification(
            user_id="assignee1",
            task_id="task1",
            task_title="Test Task",
            project_id="proj1"
        )
        
        assert result is not None


def test_notification_service_mark_as_read():
    """Test marking notification as read"""
    from app.services.notification_service import NotificationService
    
    service = NotificationService()
    
    with patch.object(service.client, 'table') as mock_table:
        mock_chain = MagicMock()
        mock_chain.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
            "id": "notif1",
            "read": True
        }]
        mock_table.return_value = mock_chain
        
        result = service.mark_as_read("notif1", "user1")
        
        assert result == True


def test_notification_service_get_unread_count():
    """Test getting unread notification count"""
    from app.services.notification_service import NotificationService
    
    service = NotificationService()
    
    with patch.object(service.client, 'table') as mock_table:
        mock_chain = MagicMock()
        mock_chain.select.return_value.eq.return_value.eq.return_value.execute.return_value.count = 5
        mock_table.return_value = mock_chain
        
        result = service.get_unread_count("user1")
        
        assert result == 5


# ============================================================================
# User Service Tests (currently 19% coverage)
# ============================================================================

def test_user_service_get_user_by_email():
    """Test getting user by email"""
    from app.services.user_service import UserService
    
    with patch('app.services.user_service.SupabaseService') as mock_supa:
        mock_supa.select.return_value = [{
            "id": "user1",
            "email": "test@example.com",
            "display_name": "Test User",
            "roles": ["staff"]
        }]
        
        result = UserService.get_user_by_email("test@example.com")
        
        assert result is not None
        assert result["email"] == "test@example.com"


# ============================================================================
# Project Service Tests (currently 23% coverage)
# ============================================================================

def test_project_service_can_admin_manage():
    """Test admin management permission check"""
    from app.services.project_service import ProjectService
    
    with patch('app.services.project_service.SupabaseService') as mock_supa:
        # Mock user with admin+manager roles
        mock_supa.select.return_value = [
            {"id": "user1", "roles": ["admin", "manager"]}
        ]
        
        result = ProjectService.can_admin_manage("user1")
        assert result == True
        
        # Mock user with only admin role (should be False)
        mock_supa.select.return_value = [
            {"id": "user2", "roles": ["admin"]}
        ]
        
        result = ProjectService.can_admin_manage("user2")
        assert result == False


def test_project_service_list_all_projects():
    """Test listing all projects (admin only)"""
    from app.services.project_service import ProjectService
    
    with patch('app.services.project_service.SupabaseService') as mock_supa:
        mock_client = MagicMock()
        mock_supa.get_client.return_value = mock_client
        
        # Mock projects query
        mock_projects_chain = MagicMock()
        mock_projects_chain.select.return_value.order.return_value.execute.return_value.data = [
            {"id": "p1", "name": "Project 1", "owner_id": "owner1", "status": "active"},
            {"id": "p2", "name": "Project 2", "owner_id": "owner2", "status": "active"}
        ]
        
        # Mock users query for owners
        mock_users_chain = MagicMock()
        mock_users_chain.select.return_value.in_.return_value.execute.return_value.data = [
            {"id": "owner1", "display_name": "Owner One", "email": "owner1@test.com"},
            {"id": "owner2", "display_name": "Owner Two", "email": "owner2@test.com"}
        ]
        
        def table_side_effect(table_name):
            if table_name == "projects":
                return mock_projects_chain
            elif table_name == "users":
                return mock_users_chain
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        projects = ProjectService.list_all_projects()
        
        assert len(projects) == 2
        assert projects[0]["owner_display_name"] == "Owner One"
        assert projects[1]["owner_display_name"] == "Owner Two"


def test_project_service_get_project_by_id():
    """Test getting project by ID with user access check"""
    from app.services.project_service import ProjectService
    
    with patch('app.services.project_service.SupabaseService') as mock_supa:
        # Mock user roles
        mock_supa.select.side_effect = [
            [{"id": "user1", "roles": ["staff"]}],  # User roles
            [{"project_id": "p1", "user_id": "user1", "role": "member"}]  # Project membership with role
        ]
        
        mock_client = MagicMock()
        mock_supa.get_client.return_value = mock_client
        
        # Mock project query
        mock_project_chain = MagicMock()
        mock_project_chain.select.return_value.eq.return_value.execute.return_value.data = [{
            "id": "p1",
            "name": "Test Project",
            "owner_id": "owner1",
            "status": "active"
        }]
        
        # Mock owner query
        mock_owner_chain = MagicMock()
        mock_owner_chain.select.return_value.in_.return_value.execute.return_value.data = [{
            "id": "owner1",
            "display_name": "Owner",
            "email": "owner@test.com"
        }]
        
        def table_side_effect(table_name):
            if table_name == "projects":
                return mock_project_chain
            elif table_name == "users":
                return mock_owner_chain
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        project = ProjectService.get_project_by_id("p1", "user1")
        
        assert project is not None
        assert project["name"] == "Test Project"
        assert project["user_role"] == "member"


def test_project_service_archive_project():
    """Test archiving a project"""
    from app.services.project_service import ProjectService
    
    with patch('app.services.project_service.SupabaseService') as mock_supa:
        # Mock user is owner
        mock_supa.select.return_value = [{"id": "user1", "roles": []}]
        
        mock_client = MagicMock()
        mock_supa.get_client.return_value = mock_client
        
        # Mock project query
        mock_project_chain = MagicMock()
        mock_project_chain.select.return_value.eq.return_value.execute.return_value.data = [{
            "id": "p1",
            "name": "Test Project",
            "owner_id": "user1",
            "status": "active"
        }]
        
        # Mock update
        mock_update_chain = MagicMock()
        mock_update_chain.update.return_value.eq.return_value.execute.return_value.data = [{
            "id": "p1",
            "status": "archived"
        }]
        
        call_count = 0
        def table_side_effect(table_name):
            nonlocal call_count
            if table_name == "projects":
                call_count += 1
                if call_count == 1:
                    return mock_project_chain
                else:
                    return mock_update_chain
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        result = ProjectService.archive_project("p1", "user1")
        
        assert result is not None


# End of coverage boost tests
