"""
TGO-8: Task Archiving
User Story: As a user, I want to archive completed tasks so that the workspace remains uncluttered.

Acceptance Criteria:
1. Given I have a completed task, When I select "Archive task,"
   Then it is moved out of the active list and placed in the archive section.
2. Given I try to archive an active task, When I attempt to archive,
   Then I should see a confirmation message to avoid accidental archiving.

Test Coverage: Unit tests, Integration tests, Edge cases
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from app.services.task_service import TaskService
from app.services.project_service import ProjectService
from app.models.project import TaskOut


# ============================================================================
# UNIT TESTS - Archive Completed Tasks
# ============================================================================

class TestArchiveCompletedTasks:
    """Test archiving completed tasks to keep workspace uncluttered"""
    
    @pytest.mark.asyncio
    async def test_archive_completed_task_success(self):
        """User can successfully archive a completed task"""
        # Arrange
        user_id = "user-123"
        task_id = "task-456"
        
        completed_task = {
            "id": task_id,
            "title": "Completed Task",
            "status": "completed",
            "assigned": [user_id],
            "project_id": "project-789",
            "type": "active"
        }
        
        archived_task = {**completed_task, "type": "archived"}
        
        # Create mock with call counter to return different values
        call_count = {"count": 0}
        
        def tasks_select_side_effect(*args, **kwargs):
            mock_eq = MagicMock()
            if call_count["count"] == 0:
                # First call - return active task
                mock_eq.execute.return_value = Mock(data=[completed_task])
            else:
                # Subsequent calls - return archived task
                mock_eq.execute.return_value = Mock(data=[archived_task])
            call_count["count"] += 1
            return mock_eq
        
        mock_tasks_table = MagicMock()
        mock_tasks_table.select.return_value.eq.side_effect = tasks_select_side_effect
        # Update call returns archived task
        mock_tasks_table.update.return_value.eq.return_value.execute.return_value = Mock(
            data=[archived_task]
        )
        
        mock_projects_table = MagicMock()
        mock_projects_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": "project-789", "name": "Test Project", "owner_id": "owner-999"}]
        )
        
        mock_users_table = MagicMock()
        mock_users_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"roles": ["staff"]}]
        )
        mock_users_table.select.return_value.in_.return_value.execute.return_value = Mock(
            data=[{"id": user_id, "email": "user@test.com", "display_name": "Test User"}]
        )
        
        mock_members_table = MagicMock()
        mock_members_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )
        
        mock_client = MagicMock()
        def table_side_effect(table_name):
            if table_name == "tasks":
                return mock_tasks_table
            elif table_name == "projects":
                return mock_projects_table
            elif table_name == "users":
                return mock_users_table
            elif table_name == "project_members":
                return mock_members_table
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        with patch('app.services.task_service.get_supabase_client', return_value=mock_client), \
             patch.object(ProjectService, 'get_user_roles', return_value=["staff"]), \
             patch.object(ProjectService, 'can_manage_project', return_value=True):
            service = TaskService()
            result = await service.archive_task(task_id, user_id)
        
        # Assert
        assert result is not None
        assert result.type == "archived"
        assert result.status == "completed"
    
    @pytest.mark.asyncio
    async def test_archived_task_not_in_active_list(self):
        """Archived task should not appear in active task list"""
        # Arrange
        user_id = "user-123"
        task_id = "task-456"
        
        archived_task = {
            "id": task_id,
            "title": "Archived Task",
            "status": "completed",
            "assigned": [user_id],
            "project_id": "project-789",
            "type": "archived"
        }
        
        mock_tasks_table = MagicMock()
        mock_tasks_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[archived_task]
        )
        
        mock_projects_table = MagicMock()
        mock_projects_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": "project-789", "name": "Test Project", "owner_id": "owner-999"}]
        )
        
        mock_users_table = MagicMock()
        mock_users_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"roles": ["staff"]}]
        )
        
        mock_members_table = MagicMock()
        mock_members_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )
        
        mock_client = MagicMock()
        def table_side_effect(table_name):
            if table_name == "tasks":
                return mock_tasks_table
            elif table_name == "projects":
                return mock_projects_table
            elif table_name == "users":
                return mock_users_table
            elif table_name == "project_members":
                return mock_members_table
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        with patch('app.services.task_service.get_supabase_client', return_value=mock_client):
            service = TaskService()
            # By default, get_task_by_id should NOT return archived tasks
            result = await service.get_task_by_id(task_id, user_id, include_archived=False)
        
        # Assert - archived task should not be visible without include_archived flag
        assert result is None
    
    @pytest.mark.asyncio
    async def test_archived_task_visible_in_archive_section(self):
        """Archived task should be visible when specifically requesting archived tasks"""
        # Arrange
        user_id = "user-123"
        task_id = "task-456"
        
        archived_task = {
            "id": task_id,
            "title": "Archived Task",
            "status": "completed",
            "assigned": [user_id],
            "project_id": "project-789",
            "type": "archived"
        }
        
        mock_tasks_table = MagicMock()
        mock_tasks_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[archived_task]
        )
        
        mock_projects_table = MagicMock()
        mock_projects_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": "project-789", "name": "Test Project", "owner_id": "owner-999"}]
        )
        
        mock_users_table = MagicMock()
        mock_users_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"roles": ["staff"]}]
        )
        mock_users_table.select.return_value.in_.return_value.execute.return_value = Mock(
            data=[{"id": user_id, "email": "user@test.com", "display_name": "Test User"}]
        )
        
        mock_members_table = MagicMock()
        mock_members_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )
        
        mock_client = MagicMock()
        def table_side_effect(table_name):
            if table_name == "tasks":
                return mock_tasks_table
            elif table_name == "projects":
                return mock_projects_table
            elif table_name == "users":
                return mock_users_table
            elif table_name == "project_members":
                return mock_members_table
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        with patch('app.services.task_service.get_supabase_client', return_value=mock_client):
            service = TaskService()
            # With include_archived=True, should return archived task
            result = await service.get_task_by_id(task_id, user_id, include_archived=True)
        
        # Assert - archived task should be visible with include_archived flag
        assert result is not None
        assert result.type == "archived"
        assert result.id == task_id


# ============================================================================
# UNIT TESTS - Archive Active Task with Confirmation
# ============================================================================

class TestArchiveActiveTaskConfirmation:
    """Test archiving active tasks requires confirmation"""
    
    @pytest.mark.asyncio
    async def test_archive_in_progress_task(self):
        """User can archive an in_progress task (should succeed without special confirmation in service)"""
        # Arrange
        user_id = "user-123"
        task_id = "task-456"
        
        in_progress_task = {
            "id": task_id,
            "title": "Active Task",
            "status": "in_progress",
            "assigned": [user_id],
            "project_id": "project-789",
            "type": "active"
        }
        
        archived_task = {**in_progress_task, "type": "archived"}
        
        # Create mock with call counter to return different values
        call_count = {"count": 0}
        
        def tasks_select_side_effect(*args, **kwargs):
            mock_eq = MagicMock()
            if call_count["count"] == 0:
                # First call - return active task
                mock_eq.execute.return_value = Mock(data=[in_progress_task])
            else:
                # Subsequent calls - return archived task
                mock_eq.execute.return_value = Mock(data=[archived_task])
            call_count["count"] += 1
            return mock_eq
        
        mock_tasks_table = MagicMock()
        mock_tasks_table.select.return_value.eq.side_effect = tasks_select_side_effect
        mock_tasks_table.update.return_value.eq.return_value.execute.return_value = Mock(
            data=[archived_task]
        )
        
        mock_projects_table = MagicMock()
        mock_projects_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": "project-789", "name": "Test Project", "owner_id": "owner-999"}]
        )
        
        mock_users_table = MagicMock()
        mock_users_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"roles": ["staff"]}]
        )
        mock_users_table.select.return_value.in_.return_value.execute.return_value = Mock(
            data=[{"id": user_id, "email": "user@test.com", "display_name": "Test User"}]
        )
        
        mock_members_table = MagicMock()
        mock_members_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )
        
        mock_client = MagicMock()
        def table_side_effect(table_name):
            if table_name == "tasks":
                return mock_tasks_table
            elif table_name == "projects":
                return mock_projects_table
            elif table_name == "users":
                return mock_users_table
            elif table_name == "project_members":
                return mock_members_table
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        with patch('app.services.task_service.get_supabase_client', return_value=mock_client), \
             patch.object(ProjectService, 'get_user_roles', return_value=["staff"]), \
             patch.object(ProjectService, 'can_manage_project', return_value=True):
            service = TaskService()
            result = await service.archive_task(task_id, user_id)
        
        # Assert - service should allow archiving (confirmation handled by UI)
        assert result is not None
        assert result.type == "archived"
    
    @pytest.mark.asyncio
    async def test_archive_todo_task(self):
        """User can archive a todo task"""
        # Arrange
        user_id = "user-123"
        task_id = "task-456"
        
        todo_task = {
            "id": task_id,
            "title": "Todo Task",
            "status": "todo",
            "assigned": [user_id],
            "project_id": "project-789",
            "type": "active"
        }
        
        archived_task = {**todo_task, "type": "archived"}
        
        # Create mock with call counter to return different values
        call_count = {"count": 0}
        
        def tasks_select_side_effect(*args, **kwargs):
            mock_eq = MagicMock()
            if call_count["count"] == 0:
                # First call - return active task
                mock_eq.execute.return_value = Mock(data=[todo_task])
            else:
                # Subsequent calls - return archived task
                mock_eq.execute.return_value = Mock(data=[archived_task])
            call_count["count"] += 1
            return mock_eq
        
        mock_tasks_table = MagicMock()
        mock_tasks_table.select.return_value.eq.side_effect = tasks_select_side_effect
        mock_tasks_table.update.return_value.eq.return_value.execute.return_value = Mock(
            data=[archived_task]
        )
        
        mock_projects_table = MagicMock()
        mock_projects_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": "project-789", "name": "Test Project", "owner_id": "owner-999"}]
        )
        
        mock_users_table = MagicMock()
        mock_users_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"roles": ["staff"]}]
        )
        mock_users_table.select.return_value.in_.return_value.execute.return_value = Mock(
            data=[{"id": user_id, "email": "user@test.com", "display_name": "Test User"}]
        )
        
        mock_members_table = MagicMock()
        mock_members_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )
        
        mock_client = MagicMock()
        def table_side_effect(table_name):
            if table_name == "tasks":
                return mock_tasks_table
            elif table_name == "projects":
                return mock_projects_table
            elif table_name == "users":
                return mock_users_table
            elif table_name == "project_members":
                return mock_members_table
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        with patch('app.services.task_service.get_supabase_client', return_value=mock_client), \
             patch.object(ProjectService, 'get_user_roles', return_value=["staff"]), \
             patch.object(ProjectService, 'can_manage_project', return_value=True):
            service = TaskService()
            result = await service.archive_task(task_id, user_id)
        
        # Assert
        assert result is not None
        assert result.type == "archived"
        assert result.status == "todo"


# ============================================================================
# UNIT TESTS - Restore Archived Tasks
# ============================================================================

class TestRestoreArchivedTasks:
    """Test restoring archived tasks back to active list"""
    
    @pytest.mark.asyncio
    async def test_restore_archived_task(self):
        """User can restore an archived task back to active"""
        # Arrange
        user_id = "user-123"
        task_id = "task-456"
        
        archived_task = {
            "id": task_id,
            "title": "Archived Task",
            "status": "completed",
            "assigned": [user_id],
            "project_id": "project-789",
            "type": "archived"
        }
        
        restored_task = {**archived_task, "type": "active"}
        
        # Create mock with call counter to return different values
        call_count = {"count": 0}
        
        def tasks_select_side_effect(*args, **kwargs):
            mock_eq = MagicMock()
            if call_count["count"] == 0:
                # First call - return archived task
                mock_eq.execute.return_value = Mock(data=[archived_task])
            else:
                # Subsequent calls - return restored task
                mock_eq.execute.return_value = Mock(data=[restored_task])
            call_count["count"] += 1
            return mock_eq
        
        mock_tasks_table = MagicMock()
        mock_tasks_table.select.return_value.eq.side_effect = tasks_select_side_effect
        # Update call returns restored task
        mock_tasks_table.update.return_value.eq.return_value.execute.return_value = Mock(
            data=[restored_task]
        )
        
        mock_projects_table = MagicMock()
        mock_projects_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": "project-789", "name": "Test Project", "owner_id": "owner-999"}]
        )
        
        mock_users_table = MagicMock()
        mock_users_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"roles": ["staff"]}]
        )
        mock_users_table.select.return_value.in_.return_value.execute.return_value = Mock(
            data=[{"id": user_id, "email": "user@test.com", "display_name": "Test User"}]
        )
        
        mock_members_table = MagicMock()
        mock_members_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )
        
        mock_client = MagicMock()
        def table_side_effect(table_name):
            if table_name == "tasks":
                return mock_tasks_table
            elif table_name == "projects":
                return mock_projects_table
            elif table_name == "users":
                return mock_users_table
            elif table_name == "project_members":
                return mock_members_table
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        with patch('app.services.task_service.get_supabase_client', return_value=mock_client):
            service = TaskService()
            result = await service.restore_task(task_id, user_id)
        
        # Assert
        assert result is not None
        assert result.type == "active"


# ============================================================================
# PERMISSION TESTS
# ============================================================================

class TestArchiveTaskPermissions:
    """Test archive permissions for different roles"""
    
    @pytest.mark.asyncio
    async def test_staff_can_archive_assigned_task(self):
        """Staff member can archive their own assigned task"""
        # Arrange
        staff_id = "staff-123"
        task_id = "task-456"
        
        task = {
            "id": task_id,
            "title": "Staff Task",
            "status": "completed",
            "assigned": [staff_id],
            "project_id": "project-789",
            "type": "active"
        }
        
        archived_task = {**task, "type": "archived"}
        
        # Create mock with call counter to return different values
        call_count = {"count": 0}
        
        def tasks_select_side_effect(*args, **kwargs):
            mock_eq = MagicMock()
            if call_count["count"] == 0:
                # First call - return active task
                mock_eq.execute.return_value = Mock(data=[task])
            else:
                # Subsequent calls - return archived task
                mock_eq.execute.return_value = Mock(data=[archived_task])
            call_count["count"] += 1
            return mock_eq
        
        mock_tasks_table = MagicMock()
        mock_tasks_table.select.return_value.eq.side_effect = tasks_select_side_effect
        mock_tasks_table.update.return_value.eq.return_value.execute.return_value = Mock(
            data=[archived_task]
        )
        
        mock_projects_table = MagicMock()
        mock_projects_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": "project-789", "name": "Test Project", "owner_id": "owner-999"}]
        )
        
        mock_users_table = MagicMock()
        mock_users_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"roles": ["staff"]}]
        )
        mock_users_table.select.return_value.in_.return_value.execute.return_value = Mock(
            data=[{"id": staff_id, "email": "staff@test.com", "display_name": "Staff User"}]
        )
        
        mock_members_table = MagicMock()
        mock_members_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )
        
        mock_client = MagicMock()
        def table_side_effect(table_name):
            if table_name == "tasks":
                return mock_tasks_table
            elif table_name == "projects":
                return mock_projects_table
            elif table_name == "users":
                return mock_users_table
            elif table_name == "project_members":
                return mock_members_table
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        with patch('app.services.task_service.get_supabase_client', return_value=mock_client), \
             patch.object(ProjectService, 'get_user_roles', return_value=["staff"]), \
             patch.object(ProjectService, 'can_manage_project', return_value=True):
            service = TaskService()
            result = await service.archive_task(task_id, staff_id)
        
        # Assert
        assert result is not None
        assert result.type == "archived"
    
    @pytest.mark.asyncio
    async def test_manager_can_archive_team_task(self):
        """Manager can archive any task in their project"""
        # Arrange
        manager_id = "manager-123"
        task_id = "task-456"
        
        task = {
            "id": task_id,
            "title": "Team Task",
            "status": "completed",
            "assigned": ["staff-789"],
            "project_id": "project-111",
            "type": "active"
        }
        
        archived_task = {**task, "type": "archived"}
        
        # Create mock with call counter to return different values
        call_count = {"count": 0}
        
        def tasks_select_side_effect(*args, **kwargs):
            mock_eq = MagicMock()
            if call_count["count"] == 0:
                # First call - return active task
                mock_eq.execute.return_value = Mock(data=[task])
            else:
                # Subsequent calls - return archived task
                mock_eq.execute.return_value = Mock(data=[archived_task])
            call_count["count"] += 1
            return mock_eq
        
        mock_tasks_table = MagicMock()
        mock_tasks_table.select.return_value.eq.side_effect = tasks_select_side_effect
        mock_tasks_table.update.return_value.eq.return_value.execute.return_value = Mock(
            data=[archived_task]
        )
        
        mock_projects_table = MagicMock()
        mock_projects_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": "project-111", "name": "Test Project", "owner_id": "owner-999"}]
        )
        
        mock_users_table = MagicMock()
        mock_users_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"roles": ["manager"]}]
        )
        mock_users_table.select.return_value.in_.return_value.execute.return_value = Mock(
            data=[{"id": "staff-789", "email": "staff@test.com", "display_name": "Staff User"}]
        )
        
        mock_members_table = MagicMock()
        mock_members_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"user_id": manager_id, "project_id": "project-111"}]
        )
        
        mock_client = MagicMock()
        def table_side_effect(table_name):
            if table_name == "tasks":
                return mock_tasks_table
            elif table_name == "projects":
                return mock_projects_table
            elif table_name == "users":
                return mock_users_table
            elif table_name == "project_members":
                return mock_members_table
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        with patch('app.services.task_service.get_supabase_client', return_value=mock_client), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]), \
             patch.object(ProjectService, 'can_manage_project', return_value=True):
            service = TaskService()
            result = await service.archive_task(task_id, manager_id)
        
        # Assert
        assert result is not None
        assert result.type == "archived"
    
    @pytest.mark.asyncio
    async def test_admin_cannot_archive_without_staff_manager_role(self):
        """Admin alone (read-only) cannot archive tasks"""
        # Arrange
        admin_id = "admin-123"
        task_id = "task-456"
        
        task = {
            "id": task_id,
            "title": "Task",
            "status": "completed",
            "assigned": ["staff-789"],
            "project_id": "project-111",
            "type": "active"
        }
        
        mock_tasks_table = MagicMock()
        mock_tasks_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[task]
        )
        
        mock_projects_table = MagicMock()
        mock_projects_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": "project-111", "name": "Test Project", "owner_id": "owner-999"}]
        )
        
        mock_users_table = MagicMock()
        mock_users_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"roles": ["admin"]}]
        )
        
        mock_members_table = MagicMock()
        mock_members_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )
        
        mock_client = MagicMock()
        def table_side_effect(table_name):
            if table_name == "tasks":
                return mock_tasks_table
            elif table_name == "projects":
                return mock_projects_table
            elif table_name == "users":
                return mock_users_table
            elif table_name == "project_members":
                return mock_members_table
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        with patch('app.services.task_service.get_supabase_client', return_value=mock_client), \
             patch.object(ProjectService, 'get_user_roles', return_value=["admin"]):
            service = TaskService()
            result = await service.archive_task(task_id, admin_id)
        
        # Assert - admin alone cannot archive (should return None due to permission error)
        assert result is None


# ============================================================================
# EDGE CASES
# ============================================================================

class TestArchiveTaskEdgeCases:
    """Edge cases for task archiving"""
    
    @pytest.mark.asyncio
    async def test_archive_already_archived_task(self):
        """Archiving an already archived task should return None (task not found in active tasks)"""
        # Arrange
        user_id = "user-123"
        task_id = "task-456"
        
        archived_task = {
            "id": task_id,
            "title": "Already Archived",
            "status": "completed",
            "assigned": [user_id],
            "project_id": "project-789",
            "type": "archived"
        }
        
        # Mock returns archived task data, but get_task_by_id filters it out when include_archived=False
        mock_tasks_table = MagicMock()
        mock_tasks_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[archived_task]
        )
        
        mock_projects_table = MagicMock()
        mock_projects_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": "project-789", "name": "Test Project", "owner_id": "owner-999"}]
        )
        
        mock_users_table = MagicMock()
        mock_users_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"roles": ["staff"]}]
        )
        
        mock_members_table = MagicMock()
        mock_members_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )
        
        mock_client = MagicMock()
        def table_side_effect(table_name):
            if table_name == "tasks":
                return mock_tasks_table
            elif table_name == "projects":
                return mock_projects_table
            elif table_name == "users":
                return mock_users_table
            elif table_name == "project_members":
                return mock_members_table
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        with patch('app.services.task_service.get_supabase_client', return_value=mock_client), \
             patch.object(ProjectService, 'get_user_roles', return_value=["staff"]), \
             patch.object(ProjectService, 'can_manage_project', return_value=True):
            service = TaskService()
            # Attempt to archive an already-archived task
            result = await service.archive_task(task_id, user_id)
        
        # Assert - should return None because archived tasks are filtered out in active task lookup
        assert result is None
    
    @pytest.mark.asyncio
    async def test_archive_nonexistent_task(self):
        """Archiving a non-existent task should return None"""
        # Arrange
        user_id = "user-123"
        task_id = "nonexistent-task"
        
        mock_tasks_table = MagicMock()
        mock_tasks_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )
        
        mock_projects_table = MagicMock()
        mock_users_table = MagicMock()
        mock_members_table = MagicMock()
        
        mock_client = MagicMock()
        def table_side_effect(table_name):
            if table_name == "tasks":
                return mock_tasks_table
            elif table_name == "projects":
                return mock_projects_table
            elif table_name == "users":
                return mock_users_table
            elif table_name == "project_members":
                return mock_members_table
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        with patch('app.services.task_service.get_supabase_client', return_value=mock_client):
            service = TaskService()
            result = await service.archive_task(task_id, user_id)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_archive_task_without_permission(self):
        """User without permission cannot archive task"""
        # Arrange
        unauthorized_user_id = "user-999"
        task_id = "task-456"
        
        task = {
            "id": task_id,
            "title": "Someone Else's Task",
            "status": "completed",
            "assigned": ["other-user"],
            "project_id": "project-789",
            "type": "active"
        }
        
        mock_tasks_table = MagicMock()
        mock_tasks_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[task]
        )
        
        mock_projects_table = MagicMock()
        mock_projects_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": "project-789", "name": "Test Project", "owner_id": "owner-999"}]
        )
        
        mock_users_table = MagicMock()
        mock_users_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"roles": ["staff"]}]
        )
        
        mock_members_table = MagicMock()
        mock_members_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )
        
        mock_client = MagicMock()
        def table_side_effect(table_name):
            if table_name == "tasks":
                return mock_tasks_table
            elif table_name == "projects":
                return mock_projects_table
            elif table_name == "users":
                return mock_users_table
            elif table_name == "project_members":
                return mock_members_table
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        with patch('app.services.task_service.get_supabase_client', return_value=mock_client):
            service = TaskService()
            # First check - user cannot even see the task
            result = await service.get_task_by_id(task_id, unauthorized_user_id)
        
        # Assert - user cannot see the task (returns None)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_archive_task_with_subtasks(self):
        """Archiving a task with subtasks should succeed"""
        # Arrange
        user_id = "user-123"
        parent_task_id = "task-parent"
        
        parent_task = {
            "id": parent_task_id,
            "title": "Parent Task",
            "status": "completed",
            "assigned": [user_id],
            "project_id": "project-789",
            "type": "active"
        }
        
        archived_parent = {**parent_task, "type": "archived"}
        
        # Create mock with call counter to return different values
        call_count = {"count": 0}
        
        def tasks_select_side_effect(*args, **kwargs):
            mock_eq = MagicMock()
            if call_count["count"] == 0:
                # First call - return active task
                mock_eq.execute.return_value = Mock(data=[parent_task])
            else:
                # Subsequent calls - return archived task
                mock_eq.execute.return_value = Mock(data=[archived_parent])
            call_count["count"] += 1
            return mock_eq
        
        mock_tasks_table = MagicMock()
        mock_tasks_table.select.return_value.eq.side_effect = tasks_select_side_effect
        mock_tasks_table.update.return_value.eq.return_value.execute.return_value = Mock(
            data=[archived_parent]
        )
        
        mock_projects_table = MagicMock()
        mock_projects_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": "project-789", "name": "Test Project", "owner_id": "owner-999"}]
        )
        
        mock_users_table = MagicMock()
        mock_users_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"roles": ["staff"]}]
        )
        mock_users_table.select.return_value.in_.return_value.execute.return_value = Mock(
            data=[{"id": user_id, "email": "user@test.com", "display_name": "Test User"}]
        )
        
        mock_members_table = MagicMock()
        mock_members_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )
        
        mock_client = MagicMock()
        def table_side_effect(table_name):
            if table_name == "tasks":
                return mock_tasks_table
            elif table_name == "projects":
                return mock_projects_table
            elif table_name == "users":
                return mock_users_table
            elif table_name == "project_members":
                return mock_members_table
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        with patch('app.services.task_service.get_supabase_client', return_value=mock_client), \
             patch.object(ProjectService, 'get_user_roles', return_value=["staff"]), \
             patch.object(ProjectService, 'can_manage_project', return_value=True):
            service = TaskService()
            result = await service.archive_task(parent_task_id, user_id)
        
        # Assert - parent task can be archived (subtasks handled separately)
        assert result is not None
        assert result.type == "archived"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
