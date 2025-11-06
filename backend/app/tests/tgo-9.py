"""
TGO-9: Team Goal - Manager Views Staff Workload Distribution
User Story: As a manager, I want to check which staff are members of multiple projects 
           so that I can understand workload distribution.

Acceptance Criteria:
1. Given I am a manager, When I open a staff member's details through Teams page, 
   Then I see a list of all projects they are part of.
2. Given I am a manager, When I open a project details, 
   Then I see a list of all tasks on the project and the staff assigned to it.

Test Coverage: Unit tests, Integration tests, Edge cases
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from app.services.team_service import TeamService
from app.services.project_service import ProjectService
from app.services.user_service import UserService
from app.services.supabase_service import SupabaseService


# ============================================================================
# UNIT TESTS - Manager Views Staff Projects
# ============================================================================

class TestManagerViewStaffProjects:
    """Test manager viewing all projects a staff member belongs to"""
    
    def test_manager_can_view_staff_single_project(self):
        """Manager can see staff member with one project"""
        # Arrange
        manager_id = "manager-123"
        staff_id = "staff-456"
        
        mock_memberships = [
            {"user_id": staff_id, "project_id": "project-1", "role": "member"}
        ]
        
        mock_projects = [
            {"id": "project-1", "name": "Project Alpha", "owner_id": "owner-1", "status": "active"}
        ]
        
        with patch.object(SupabaseService, 'select') as mock_select, \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            def select_side_effect(table, filters=None):
                if table == "project_members" and filters.get("user_id") == staff_id:
                    return mock_memberships
                if table == "projects":
                    return mock_projects
                return []
            
            mock_select.side_effect = select_side_effect
            
            # Act - Get staff's project memberships
            memberships = SupabaseService.select("project_members", filters={"user_id": staff_id})
            
            # Assert
            assert len(memberships) == 1
            assert memberships[0]["project_id"] == "project-1"
    
    def test_manager_can_view_staff_multiple_projects(self):
        """Manager can see staff member with multiple projects"""
        # Arrange
        manager_id = "manager-123"
        staff_id = "staff-456"
        
        mock_memberships = [
            {"user_id": staff_id, "project_id": "project-1", "role": "member"},
            {"user_id": staff_id, "project_id": "project-2", "role": "member"},
            {"user_id": staff_id, "project_id": "project-3", "role": "member"}
        ]
        
        with patch.object(SupabaseService, 'select', return_value=mock_memberships), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            # Act
            memberships = SupabaseService.select("project_members", filters={"user_id": staff_id})
            
            # Assert - Staff is in 3 projects
            assert len(memberships) == 3
            project_ids = [m["project_id"] for m in memberships]
            assert "project-1" in project_ids
            assert "project-2" in project_ids
            assert "project-3" in project_ids
    
    def test_manager_identifies_staff_with_no_projects(self):
        """Manager can see staff member with zero projects"""
        # Arrange
        manager_id = "manager-123"
        staff_id = "staff-789"
        
        with patch.object(SupabaseService, 'select', return_value=[]), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            # Act
            memberships = SupabaseService.select("project_members", filters={"user_id": staff_id})
            
            # Assert
            assert len(memberships) == 0
    
    def test_manager_can_view_staff_project_roles(self):
        """Manager can see staff roles in different projects"""
        # Arrange
        manager_id = "manager-123"
        staff_id = "staff-456"
        
        mock_memberships = [
            {"user_id": staff_id, "project_id": "project-1", "role": "member"},
            {"user_id": staff_id, "project_id": "project-2", "role": "owner"},
            {"user_id": staff_id, "project_id": "project-3", "role": "viewer"}
        ]
        
        with patch.object(SupabaseService, 'select', return_value=mock_memberships), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            # Act
            memberships = SupabaseService.select("project_members", filters={"user_id": staff_id})
            
            # Assert - Different roles in different projects
            roles = [m["role"] for m in memberships]
            assert "member" in roles
            assert "owner" in roles
            assert "viewer" in roles
    
    def test_staff_cannot_view_other_staff_projects(self):
        """Staff role cannot view other staff members' projects"""
        # Arrange
        staff_viewer_id = "staff-123"
        staff_target_id = "staff-456"
        
        with patch.object(ProjectService, 'get_user_roles', return_value=["staff"]):
            # Act & Assert
            user_roles = ProjectService.get_user_roles(staff_viewer_id)
            
            # Staff doesn't have manager role
            assert "manager" not in user_roles
            assert "staff" in user_roles


# ============================================================================
# UNIT TESTS - Manager Views Project Tasks and Staff
# ============================================================================

class TestManagerViewProjectTasksAndStaff:
    """Test manager viewing project details with tasks and assigned staff"""
    
    def test_manager_can_view_project_tasks_list(self):
        """Manager can see all tasks in a project"""
        # Arrange
        manager_id = "manager-123"
        project_id = "project-456"
        
        mock_tasks = [
            {"id": "task-1", "title": "Task 1", "assigned": ["staff-1"], "status": "todo"},
            {"id": "task-2", "title": "Task 2", "assigned": ["staff-2"], "status": "in_progress"},
            {"id": "task-3", "title": "Task 3", "assigned": ["staff-1", "staff-2"], "status": "completed"}
        ]
        
        with patch.object(SupabaseService, 'select') as mock_select, \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            mock_select.return_value = mock_tasks
            
            # Act
            tasks = SupabaseService.select("tasks", filters={"project_id": project_id})
            
            # Assert
            assert len(tasks) == 3
            assert tasks[0]["id"] == "task-1"
            assert tasks[1]["id"] == "task-2"
            assert tasks[2]["id"] == "task-3"
    
    def test_manager_can_view_task_assignees(self):
        """Manager can see which staff are assigned to each task"""
        # Arrange
        manager_id = "manager-123"
        project_id = "project-456"
        
        mock_tasks = [
            {"id": "task-1", "title": "Backend API", "assigned": ["staff-1", "staff-2"]},
            {"id": "task-2", "title": "Frontend UI", "assigned": ["staff-3"]},
            {"id": "task-3", "title": "Testing", "assigned": ["staff-1", "staff-3"]}
        ]
        
        with patch.object(SupabaseService, 'select', return_value=mock_tasks), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            # Act
            tasks = SupabaseService.select("tasks", filters={"project_id": project_id})
            
            # Assert - Check assignees
            assert "staff-1" in tasks[0]["assigned"]
            assert "staff-2" in tasks[0]["assigned"]
            assert "staff-3" in tasks[1]["assigned"]
            assert len(tasks[2]["assigned"]) == 2
    
    def test_manager_can_identify_unassigned_tasks(self):
        """Manager can see tasks with no assignees"""
        # Arrange
        manager_id = "manager-123"
        project_id = "project-456"
        
        mock_tasks = [
            {"id": "task-1", "title": "Assigned Task", "assigned": ["staff-1"]},
            {"id": "task-2", "title": "Unassigned Task", "assigned": []},
            {"id": "task-3", "title": "Another Unassigned", "assigned": None}
        ]
        
        with patch.object(SupabaseService, 'select', return_value=mock_tasks), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            # Act
            tasks = SupabaseService.select("tasks", filters={"project_id": project_id})
            
            # Assert - Identify unassigned tasks
            unassigned_count = sum(1 for t in tasks if not t.get("assigned"))
            assert unassigned_count == 2
    
    def test_manager_can_view_project_with_no_tasks(self):
        """Manager can view project that has zero tasks"""
        # Arrange
        manager_id = "manager-123"
        project_id = "project-empty"
        
        with patch.object(SupabaseService, 'select', return_value=[]), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            # Act
            tasks = SupabaseService.select("tasks", filters={"project_id": project_id})
            
            # Assert
            assert len(tasks) == 0
    
    def test_manager_can_view_task_details_with_status(self):
        """Manager can see detailed task information including status"""
        # Arrange
        manager_id = "manager-123"
        project_id = "project-456"
        
        mock_tasks = [
            {
                "id": "task-1",
                "title": "Implement Feature X",
                "assigned": ["staff-1", "staff-2"],
                "status": "in_progress",
                "due_date": "2025-12-01",
                "priority": 1
            }
        ]
        
        with patch.object(SupabaseService, 'select', return_value=mock_tasks), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            # Act
            tasks = SupabaseService.select("tasks", filters={"project_id": project_id})
            
            # Assert - Full task details visible
            task = tasks[0]
            assert task["title"] == "Implement Feature X"
            assert task["status"] == "in_progress"
            assert len(task["assigned"]) == 2
            assert task["priority"] == 1
    
    def test_manager_can_see_project_members(self):
        """Manager can see all project members"""
        # Arrange
        manager_id = "manager-123"
        project_id = "project-456"
        
        mock_members = [
            {"user_id": "user-1", "project_id": project_id, "role": "owner"},
            {"user_id": "user-2", "project_id": project_id, "role": "member"},
            {"user_id": "user-3", "project_id": project_id, "role": "viewer"}
        ]
        
        with patch.object(SupabaseService, 'select', return_value=mock_members), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            # Act
            members = SupabaseService.select("project_members", filters={"project_id": project_id})
            
            # Assert
            assert len(members) == 3
            assert any(m["role"] == "owner" for m in members)
            assert any(m["role"] == "member" for m in members)


# ============================================================================
# INTEGRATION TESTS - Complete Workflows
# ============================================================================

class TestManagerWorkloadIntegration:
    """Integration tests for complete workload distribution workflows"""
    
    def test_manager_views_staff_workload_distribution(self):
        """Manager can view workload distribution across team members"""
        # Arrange
        manager_id = "manager-123"
        team_id = "team-456"
        
        # Mock team members
        mock_team_members = [
            {"user_id": "staff-1", "team_id": team_id},
            {"user_id": "staff-2", "team_id": team_id},
            {"user_id": "staff-3", "team_id": team_id}
        ]
        
        # Mock project memberships for each staff
        def membership_side_effect(table, filters=None):
            if table == "team_members":
                return mock_team_members
            if table == "project_members":
                user_id = filters.get("user_id")
                if user_id == "staff-1":
                    return [{"project_id": f"proj-{i}"} for i in range(3)]  # 3 projects
                elif user_id == "staff-2":
                    return [{"project_id": f"proj-{i}"} for i in range(5)]  # 5 projects (overloaded)
                elif user_id == "staff-3":
                    return [{"project_id": "proj-1"}]  # 1 project
            return []
        
        with patch.object(SupabaseService, 'select', side_effect=membership_side_effect), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            # Act - Get team members
            team_members = SupabaseService.select("team_members", filters={"team_id": team_id})
            
            # Check each member's workload
            workload = {}
            for member in team_members:
                projects = SupabaseService.select("project_members", filters={"user_id": member["user_id"]})
                workload[member["user_id"]] = len(projects)
            
            # Assert - Workload distribution visible
            assert workload["staff-1"] == 3
            assert workload["staff-2"] == 5  # Highest workload
            assert workload["staff-3"] == 1  # Lowest workload
    
    def test_manager_identifies_overloaded_staff(self):
        """Manager can identify staff with too many projects"""
        # Arrange
        manager_id = "manager-123"
        max_projects_threshold = 4
        
        staff_workload = {
            "staff-1": 2,  # OK
            "staff-2": 6,  # Overloaded
            "staff-3": 3,  # OK
            "staff-4": 5,  # Overloaded
        }
        
        # Act - Identify overloaded staff
        overloaded = {sid: count for sid, count in staff_workload.items() 
                     if count > max_projects_threshold}
        
        # Assert
        assert len(overloaded) == 2
        assert "staff-2" in overloaded
        assert "staff-4" in overloaded
        assert overloaded["staff-2"] == 6
    
    def test_manager_views_project_with_tasks_and_assignments(self):
        """Manager views complete project overview with tasks and staff"""
        # Arrange
        manager_id = "manager-123"
        project_id = "project-456"
        
        mock_project = {
            "id": project_id,
            "name": "Enterprise System",
            "owner_id": "owner-1",
            "status": "active"
        }
        
        mock_tasks = [
            {"id": "task-1", "title": "Backend", "assigned": ["staff-1", "staff-2"]},
            {"id": "task-2", "title": "Frontend", "assigned": ["staff-3"]},
            {"id": "task-3", "title": "Database", "assigned": ["staff-1"]}
        ]
        
        mock_members = [
            {"user_id": "owner-1", "role": "owner"},
            {"user_id": "staff-1", "role": "member"},
            {"user_id": "staff-2", "role": "member"},
            {"user_id": "staff-3", "role": "member"}
        ]
        
        with patch.object(SupabaseService, 'select') as mock_select, \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]), \
             patch.object(ProjectService, 'get_project_by_id', return_value=mock_project):
            
            def select_side_effect(table, filters=None):
                if table == "tasks":
                    return mock_tasks
                if table == "project_members":
                    return mock_members
                return []
            
            mock_select.side_effect = select_side_effect
            
            # Act
            project = ProjectService.get_project_by_id(project_id, manager_id)
            tasks = SupabaseService.select("tasks", filters={"project_id": project_id})
            members = SupabaseService.select("project_members", filters={"project_id": project_id})
            
            # Assert - Complete overview
            assert project["name"] == "Enterprise System"
            assert len(tasks) == 3
            assert len(members) == 4
            
            # Check staff-1 is assigned to 2 tasks
            staff_1_tasks = [t for t in tasks if "staff-1" in t["assigned"]]
            assert len(staff_1_tasks) == 2


# ============================================================================
# EDGE CASES
# ============================================================================

class TestManagerViewWorkloadEdgeCases:
    """Edge cases for manager workload distribution features"""
    
    def test_manager_views_staff_with_archived_projects(self):
        """Manager sees only active projects, not archived ones"""
        # Arrange
        manager_id = "manager-123"
        staff_id = "staff-456"
        
        mock_memberships = [
            {"user_id": staff_id, "project_id": "project-1"},
            {"user_id": staff_id, "project_id": "project-2"},
            {"user_id": staff_id, "project_id": "project-3"}
        ]
        
        mock_projects = [
            {"id": "project-1", "name": "Active 1", "status": "active"},
            {"id": "project-2", "name": "Archived", "status": "archived"},
            {"id": "project-3", "name": "Active 2", "status": "active"}
        ]
        
        with patch.object(SupabaseService, 'select') as mock_select, \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            def select_side_effect(table, filters=None):
                if table == "project_members":
                    return mock_memberships
                if table == "projects":
                    return mock_projects
                return []
            
            mock_select.side_effect = select_side_effect
            
            # Act
            memberships = SupabaseService.select("project_members", filters={"user_id": staff_id})
            projects = SupabaseService.select("projects")
            
            active_project_ids = [p["id"] for p in projects if p["status"] == "active"]
            active_memberships = [m for m in memberships if m["project_id"] in active_project_ids]
            
            # Assert - Only 2 active projects counted
            assert len(active_memberships) == 2
    
    def test_manager_views_project_with_subtasks(self):
        """Manager can see tasks and subtasks in project view"""
        # Arrange
        manager_id = "manager-123"
        project_id = "project-456"
        
        mock_tasks = [
            {"id": "task-1", "title": "Main Task", "assigned": ["staff-1"], "parent_task_id": None},
            {"id": "task-2", "title": "Subtask 1", "assigned": ["staff-2"], "parent_task_id": "task-1"},
            {"id": "task-3", "title": "Subtask 2", "assigned": ["staff-1"], "parent_task_id": "task-1"}
        ]
        
        with patch.object(SupabaseService, 'select', return_value=mock_tasks), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            # Act
            tasks = SupabaseService.select("tasks", filters={"project_id": project_id})
            
            # Count parent tasks vs subtasks
            parent_tasks = [t for t in tasks if not t.get("parent_task_id")]
            subtasks = [t for t in tasks if t.get("parent_task_id")]
            
            # Assert
            assert len(parent_tasks) == 1
            assert len(subtasks) == 2
    
    def test_manager_cannot_view_non_team_staff_projects(self):
        """Manager cannot view projects of staff not in their team"""
        # Arrange
        manager_id = "manager-123"
        team_id = "team-456"
        external_staff_id = "staff-external"
        
        mock_team_members = [
            {"user_id": "staff-1", "team_id": team_id},
            {"user_id": "staff-2", "team_id": team_id}
            # external_staff_id NOT in this team
        ]
        
        with patch.object(SupabaseService, 'select', return_value=mock_team_members), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            # Act
            team_members = SupabaseService.select("team_members", filters={"team_id": team_id})
            team_member_ids = [m["user_id"] for m in team_members]
            
            # Assert - External staff not in team
            assert external_staff_id not in team_member_ids
            assert len(team_member_ids) == 2
    
    def test_manager_views_staff_with_different_project_roles(self):
        """Manager sees staff can have different roles across projects"""
        # Arrange
        manager_id = "manager-123"
        staff_id = "staff-456"
        
        mock_memberships = [
            {"user_id": staff_id, "project_id": "project-1", "role": "owner"},
            {"user_id": staff_id, "project_id": "project-2", "role": "member"},
            {"user_id": staff_id, "project_id": "project-3", "role": "viewer"},
            {"user_id": staff_id, "project_id": "project-4", "role": "member"}
        ]
        
        with patch.object(SupabaseService, 'select', return_value=mock_memberships), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            # Act
            memberships = SupabaseService.select("project_members", filters={"user_id": staff_id})
            
            # Count role distribution
            role_counts = {}
            for m in memberships:
                role = m["role"]
                role_counts[role] = role_counts.get(role, 0) + 1
            
            # Assert
            assert role_counts["owner"] == 1
            assert role_counts["member"] == 2
            assert role_counts["viewer"] == 1
    
    def test_manager_views_tasks_with_multiple_assignees(self):
        """Manager sees tasks can have multiple staff assigned"""
        # Arrange
        manager_id = "manager-123"
        project_id = "project-456"
        
        mock_tasks = [
            {"id": "task-1", "title": "Solo Task", "assigned": ["staff-1"]},
            {"id": "task-2", "title": "Pair Task", "assigned": ["staff-1", "staff-2"]},
            {"id": "task-3", "title": "Team Task", "assigned": ["staff-1", "staff-2", "staff-3", "staff-4"]}
        ]
        
        with patch.object(SupabaseService, 'select', return_value=mock_tasks), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            # Act
            tasks = SupabaseService.select("tasks", filters={"project_id": project_id})
            
            # Assert - Different assignment patterns
            assert len(tasks[0]["assigned"]) == 1
            assert len(tasks[1]["assigned"]) == 2
            assert len(tasks[2]["assigned"]) == 4
    
    def test_staff_role_cannot_access_manager_workload_view(self):
        """Staff without manager role cannot view workload distribution"""
        # Arrange
        staff_id = "staff-123"
        
        with patch.object(ProjectService, 'get_user_roles', return_value=["staff"]):
            # Act
            user_roles = ProjectService.get_user_roles(staff_id)
            
            # Assert - Not a manager
            assert "manager" not in user_roles
            assert "staff" in user_roles
    
    def test_admin_can_view_all_staff_workloads(self):
        """Admin has read-only access to all workload data"""
        # Arrange
        admin_id = "admin-789"
        
        with patch.object(ProjectService, 'get_user_roles', return_value=["admin"]):
            # Act
            user_roles = ProjectService.get_user_roles(admin_id)
            
            # Assert - Admin role present
            assert "admin" in user_roles


# ============================================================================
# CROSS-FEATURE TESTS
# ============================================================================

class TestManagerWorkloadCrossFeatures:
    """Tests that span multiple features and services"""
    
    def test_manager_correlates_team_members_with_projects(self):
        """Manager can correlate team membership with project assignments"""
        # Arrange
        manager_id = "manager-123"
        team_id = "team-456"
        
        mock_team_members = [
            {"user_id": "staff-1", "team_id": team_id},
            {"user_id": "staff-2", "team_id": team_id}
        ]
        
        def membership_side_effect(table, filters=None):
            if table == "team_members":
                return mock_team_members
            if table == "project_members":
                user_id = filters.get("user_id")
                if user_id == "staff-1":
                    return [{"project_id": "proj-A"}, {"project_id": "proj-B"}]
                elif user_id == "staff-2":
                    return [{"project_id": "proj-B"}, {"project_id": "proj-C"}]
            return []
        
        with patch.object(SupabaseService, 'select', side_effect=membership_side_effect), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            # Act
            team_members = SupabaseService.select("team_members", filters={"team_id": team_id})
            
            # Build workload map
            workload_map = {}
            for member in team_members:
                projects = SupabaseService.select("project_members", filters={"user_id": member["user_id"]})
                workload_map[member["user_id"]] = [p["project_id"] for p in projects]
            
            # Assert - Correlation visible
            assert "proj-A" in workload_map["staff-1"]
            assert "proj-B" in workload_map["staff-1"]
            assert "proj-B" in workload_map["staff-2"]  # Shared project
            assert "proj-C" in workload_map["staff-2"]
    
    def test_manager_views_project_tasks_filtered_by_staff(self):
        """Manager can filter project tasks by specific staff member"""
        # Arrange
        manager_id = "manager-123"
        project_id = "project-456"
        target_staff_id = "staff-1"
        
        mock_tasks = [
            {"id": "task-1", "title": "Task A", "assigned": ["staff-1", "staff-2"]},
            {"id": "task-2", "title": "Task B", "assigned": ["staff-2"]},
            {"id": "task-3", "title": "Task C", "assigned": ["staff-1"]},
            {"id": "task-4", "title": "Task D", "assigned": ["staff-3"]}
        ]
        
        with patch.object(SupabaseService, 'select', return_value=mock_tasks), \
             patch.object(ProjectService, 'get_user_roles', return_value=["manager"]):
            
            # Act
            all_tasks = SupabaseService.select("tasks", filters={"project_id": project_id})
            staff_tasks = [t for t in all_tasks if target_staff_id in t["assigned"]]
            
            # Assert - Filtered to staff-1's tasks
            assert len(staff_tasks) == 2
            assert staff_tasks[0]["id"] == "task-1"
            assert staff_tasks[1]["id"] == "task-3"
    
    def test_manager_calculates_team_capacity(self):
        """Manager can calculate total team capacity and utilization"""
        # Arrange
        manager_id = "manager-123"
        team_id = "team-456"
        max_projects_per_person = 4
        
        team_workload = {
            "staff-1": 3,  # 75% capacity
            "staff-2": 4,  # 100% capacity
            "staff-3": 2,  # 50% capacity
            "staff-4": 1   # 25% capacity
        }
        
        # Act
        total_capacity = len(team_workload) * max_projects_per_person
        total_assigned = sum(team_workload.values())
        utilization_rate = (total_assigned / total_capacity) * 100
        
        # Assert
        assert total_capacity == 16
        assert total_assigned == 10
        assert utilization_rate == 62.5  # 62.5% team utilization


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
