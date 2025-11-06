"""
TGO-4: View Project Collaborators Feature Tests

User Story: As a user, I want to see which collaborators are in a project so that I know who I am working with.

Acceptance Criteria:
1. Given I am inside a project,
   When I open the "Collaborators" section,
   Then I see a list of all members with their names and roles.

2. Given I am inside a project with no collaborators,
   When I open the "Collaborators" section,
   Then I see a message like "No collaborators added yet."

This test suite includes:
- Unit tests for viewing project members
- Permission and access control tests
- Edge cases for empty projects, multiple members, etc.
- Data format and structure validation
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from typing import Dict, Any, List

from app.services.project_service import ProjectService


# ============================================================================
# UNIT TESTS - View Project Members Core Functionality
# ============================================================================

class TestViewProjectMembersUnit:
    """Unit tests for viewing project members/collaborators"""

    def test_get_project_members_returns_list_with_names_and_roles(self):
        """Test that get_project_members returns all members with their names and roles"""
        # Arrange
        project_id = "11111111-1111-1111-1111-111111111111"
        
        mock_result = Mock()
        mock_result.data = [
            {
                "project_id": project_id,
                "user_id": "user1",
                "role": "owner",
                "users": {"email": "owner@example.com", "display_name": "Project Owner"}
            },
            {
                "project_id": project_id,
                "user_id": "user2",
                "role": "manager",
                "users": {"email": "manager@example.com", "display_name": "Team Manager"}
            },
            {
                "project_id": project_id,
                "user_id": "user3",
                "role": "staff",
                "users": {"email": "staff@example.com", "display_name": "Team Member"}
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            result = ProjectService.get_project_members(project_id)
        
        # Assert
        assert len(result) == 3
        assert result[0]["user_display_name"] == "Project Owner"
        assert result[0]["role"] == "owner"
        assert result[1]["user_display_name"] == "Team Manager"
        assert result[1]["role"] == "manager"
        assert result[2]["user_display_name"] == "Team Member"
        assert result[2]["role"] == "staff"

    def test_get_project_members_returns_empty_list_for_no_collaborators(self):
        """Test that get_project_members returns empty list when project has only owner (no additional collaborators)"""
        # Arrange
        project_id = "22222222-2222-2222-2222-222222222222"
        
        mock_result = Mock()
        mock_result.data = []
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            result = ProjectService.get_project_members(project_id)
        
        # Assert
        assert result == []
        assert len(result) == 0

    def test_get_project_members_includes_all_required_fields(self):
        """Test that returned member data includes all required fields: project_id, user_id, role, email, display_name"""
        # Arrange
        project_id = "33333333-3333-3333-3333-333333333333"
        user_id = "44444444-4444-4444-4444-444444444444"
        
        mock_result = Mock()
        mock_result.data = [
            {
                "project_id": project_id,
                "user_id": user_id,
                "role": "staff",
                "users": {"email": "member@example.com", "display_name": "Team Member"}
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            result = ProjectService.get_project_members(project_id)
        
        # Assert
        assert len(result) == 1
        member = result[0]
        assert "project_id" in member
        assert "user_id" in member
        assert "role" in member
        assert "user_email" in member
        assert "user_display_name" in member
        assert member["project_id"] == project_id
        assert member["user_id"] == user_id
        assert member["role"] == "staff"
        assert member["user_email"] == "member@example.com"
        assert member["user_display_name"] == "Team Member"

    def test_get_project_members_handles_missing_user_data_gracefully(self):
        """Test that get_project_members handles missing user data (email/display_name) gracefully"""
        # Arrange
        project_id = "55555555-5555-5555-5555-555555555555"
        
        mock_result = Mock()
        mock_result.data = [
            {
                "project_id": project_id,
                "user_id": "user1",
                "role": "staff",
                "users": {}  # Empty user data
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            result = ProjectService.get_project_members(project_id)
        
        # Assert
        assert len(result) == 1
        assert result[0]["user_email"] is None
        assert result[0]["user_display_name"] is None

    def test_get_project_members_with_multiple_roles(self):
        """Test that get_project_members correctly returns members with different roles"""
        # Arrange
        project_id = "66666666-6666-6666-6666-666666666666"
        
        mock_result = Mock()
        mock_result.data = [
            {
                "project_id": project_id,
                "user_id": "owner_user",
                "role": "owner",
                "users": {"email": "owner@test.com", "display_name": "Owner User"}
            },
            {
                "project_id": project_id,
                "user_id": "manager_user",
                "role": "manager",
                "users": {"email": "manager@test.com", "display_name": "Manager User"}
            },
            {
                "project_id": project_id,
                "user_id": "staff_user1",
                "role": "staff",
                "users": {"email": "staff1@test.com", "display_name": "Staff User 1"}
            },
            {
                "project_id": project_id,
                "user_id": "staff_user2",
                "role": "staff",
                "users": {"email": "staff2@test.com", "display_name": "Staff User 2"}
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            result = ProjectService.get_project_members(project_id)
        
        # Assert
        assert len(result) == 4
        roles = [member["role"] for member in result]
        assert "owner" in roles
        assert "manager" in roles
        assert roles.count("staff") == 2


# ============================================================================
# PERMISSION TESTS - Access Control for Viewing Members
# ============================================================================

class TestViewProjectMembersPermissions:
    """Tests for permission and access control when viewing project members"""

    def test_is_project_member_returns_true_for_member(self):
        """Test that is_project_member correctly identifies a project member"""
        # Arrange
        project_id = "77777777-7777-7777-7777-777777777777"
        user_id = "88888888-8888-8888-8888-888888888888"
        
        with patch('app.services.supabase_service.SupabaseService.select') as mock_select:
            # First call is for get_user_roles (returns non-admin)
            # Second call is for checking project membership
            mock_select.side_effect = [
                [{"id": user_id, "roles": ["staff"]}],  # get_user_roles
                [{"project_id": project_id, "user_id": user_id, "role": "staff"}]  # project_members check
            ]
            
            # Act
            result = ProjectService.is_project_member(project_id, user_id)
        
        # Assert
        assert result is True
        assert mock_select.call_count == 2

    def test_is_project_member_returns_false_for_non_member(self):
        """Test that is_project_member returns False for non-members"""
        # Arrange
        project_id = "99999999-9999-9999-9999-999999999999"
        user_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        
        with patch('app.services.supabase_service.SupabaseService.select') as mock_select:
            mock_select.return_value = []  # No membership found
            
            # Act
            result = ProjectService.is_project_member(project_id, user_id)
        
        # Assert
        assert result is False

    def test_owner_can_view_project_members(self):
        """Test that project owner can view project members"""
        # Arrange
        project_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        owner_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"
        
        mock_result = Mock()
        mock_result.data = [
            {
                "project_id": project_id,
                "user_id": owner_id,
                "role": "owner",
                "users": {"email": "owner@test.com", "display_name": "Owner"}
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.select') as mock_select, \
             patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            
            # Mock is_project_member check
            mock_select.return_value = [
                {"project_id": project_id, "user_id": owner_id, "role": "owner"}
            ]
            
            # Mock get_project_members
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select_chain = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select_chain
            mock_select_chain.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            is_member = ProjectService.is_project_member(project_id, owner_id)
            members = ProjectService.get_project_members(project_id)
        
        # Assert
        assert is_member is True
        assert len(members) == 1

    def test_staff_member_can_view_project_members(self):
        """Test that staff members can view project members"""
        # Arrange
        project_id = "dddddddd-dddd-dddd-dddd-dddddddddddd"
        staff_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
        
        mock_result = Mock()
        mock_result.data = [
            {
                "project_id": project_id,
                "user_id": "owner123",
                "role": "owner",
                "users": {"email": "owner@test.com", "display_name": "Owner"}
            },
            {
                "project_id": project_id,
                "user_id": staff_id,
                "role": "staff",
                "users": {"email": "staff@test.com", "display_name": "Staff"}
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.select') as mock_select, \
             patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            
            # Mock is_project_member check
            mock_select.return_value = [
                {"project_id": project_id, "user_id": staff_id, "role": "staff"}
            ]
            
            # Mock get_project_members
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select_chain = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select_chain
            mock_select_chain.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            is_member = ProjectService.is_project_member(project_id, staff_id)
            members = ProjectService.get_project_members(project_id)
        
        # Assert
        assert is_member is True
        assert len(members) == 2

    def test_manager_can_view_project_members(self):
        """Test that managers can view project members"""
        # Arrange
        project_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
        manager_id = "12121212-1212-1212-1212-121212121212"
        
        mock_result = Mock()
        mock_result.data = [
            {
                "project_id": project_id,
                "user_id": manager_id,
                "role": "manager",
                "users": {"email": "manager@test.com", "display_name": "Manager"}
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.select') as mock_select, \
             patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            
            # Mock is_project_member check
            mock_select.return_value = [
                {"project_id": project_id, "user_id": manager_id, "role": "manager"}
            ]
            
            # Mock get_project_members
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select_chain = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select_chain
            mock_select_chain.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            is_member = ProjectService.is_project_member(project_id, manager_id)
            members = ProjectService.get_project_members(project_id)
        
        # Assert
        assert is_member is True
        assert len(members) == 1


# ============================================================================
# EDGE CASES - Boundary Conditions and Error Handling
# ============================================================================

class TestViewProjectMembersEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_get_project_members_with_nonexistent_project(self):
        """Test getting members for a project that doesn't exist returns empty list"""
        # Arrange
        nonexistent_project_id = "00000000-0000-0000-0000-000000000000"
        
        mock_result = Mock()
        mock_result.data = []
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            result = ProjectService.get_project_members(nonexistent_project_id)
        
        # Assert
        assert result == []

    def test_get_project_members_with_single_owner_only(self):
        """Test project with only owner (no additional collaborators)"""
        # Arrange
        project_id = "13131313-1313-1313-1313-131313131313"
        owner_id = "14141414-1414-1414-1414-141414141414"
        
        mock_result = Mock()
        mock_result.data = [
            {
                "project_id": project_id,
                "user_id": owner_id,
                "role": "owner",
                "users": {"email": "owner@test.com", "display_name": "Solo Owner"}
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            result = ProjectService.get_project_members(project_id)
        
        # Assert
        assert len(result) == 1
        assert result[0]["role"] == "owner"
        assert result[0]["user_display_name"] == "Solo Owner"

    def test_get_project_members_with_large_team(self):
        """Test project with many collaborators (10+ members)"""
        # Arrange
        project_id = "15151515-1515-1515-1515-151515151515"
        
        # Create 12 members
        mock_members = []
        for i in range(12):
            role = "owner" if i == 0 else "manager" if i == 1 else "staff"
            mock_members.append({
                "project_id": project_id,
                "user_id": f"user{i}",
                "role": role,
                "users": {
                    "email": f"user{i}@test.com",
                    "display_name": f"User {i}"
                }
            })
        
        mock_result = Mock()
        mock_result.data = mock_members
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            result = ProjectService.get_project_members(project_id)
        
        # Assert
        assert len(result) == 12
        assert result[0]["role"] == "owner"
        assert result[1]["role"] == "manager"
        assert result[2]["role"] == "staff"

    def test_get_project_members_with_null_result_data(self):
        """Test handling when database returns None for data"""
        # Arrange
        project_id = "16161616-1616-1616-1616-161616161616"
        
        mock_result = Mock()
        mock_result.data = None  # Simulate null data
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            result = ProjectService.get_project_members(project_id)
        
        # Assert
        assert result == []

    def test_get_project_members_preserves_all_user_data(self):
        """Test that all user data fields are preserved correctly in the response"""
        # Arrange
        project_id = "17171717-1717-1717-1717-171717171717"
        
        mock_result = Mock()
        mock_result.data = [
            {
                "project_id": project_id,
                "user_id": "user_abc",
                "role": "manager",
                "users": {
                    "email": "alice@example.com",
                    "display_name": "Alice Smith"
                }
            },
            {
                "project_id": project_id,
                "user_id": "user_def",
                "role": "staff",
                "users": {
                    "email": "bob@example.com",
                    "display_name": "Bob Johnson"
                }
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            result = ProjectService.get_project_members(project_id)
        
        # Assert
        assert result[0]["user_email"] == "alice@example.com"
        assert result[0]["user_display_name"] == "Alice Smith"
        assert result[1]["user_email"] == "bob@example.com"
        assert result[1]["user_display_name"] == "Bob Johnson"

    def test_get_project_members_handles_special_characters_in_names(self):
        """Test that special characters in display names are handled correctly"""
        # Arrange
        project_id = "18181818-1818-1818-1818-181818181818"
        
        mock_result = Mock()
        mock_result.data = [
            {
                "project_id": project_id,
                "user_id": "user1",
                "role": "staff",
                "users": {
                    "email": "user@test.com",
                    "display_name": "O'Brien, José-María"
                }
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            result = ProjectService.get_project_members(project_id)
        
        # Assert
        assert result[0]["user_display_name"] == "O'Brien, José-María"

    def test_is_project_member_with_empty_project_id(self):
        """Test is_project_member with empty project_id returns False"""
        # Arrange
        project_id = ""
        user_id = "19191919-1919-1919-1919-191919191919"
        
        with patch('app.services.supabase_service.SupabaseService.select') as mock_select:
            mock_select.return_value = []
            
            # Act
            result = ProjectService.is_project_member(project_id, user_id)
        
        # Assert
        assert result is False

    def test_get_project_members_with_multiple_managers(self):
        """Test project with multiple managers"""
        # Arrange
        project_id = "20202020-2020-2020-2020-202020202020"
        
        mock_result = Mock()
        mock_result.data = [
            {
                "project_id": project_id,
                "user_id": "owner1",
                "role": "owner",
                "users": {"email": "owner@test.com", "display_name": "Owner"}
            },
            {
                "project_id": project_id,
                "user_id": "manager1",
                "role": "manager",
                "users": {"email": "manager1@test.com", "display_name": "Manager One"}
            },
            {
                "project_id": project_id,
                "user_id": "manager2",
                "role": "manager",
                "users": {"email": "manager2@test.com", "display_name": "Manager Two"}
            },
            {
                "project_id": project_id,
                "user_id": "manager3",
                "role": "manager",
                "users": {"email": "manager3@test.com", "display_name": "Manager Three"}
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            result = ProjectService.get_project_members(project_id)
        
        # Assert
        assert len(result) == 4
        manager_count = sum(1 for m in result if m["role"] == "manager")
        assert manager_count == 3


# ============================================================================
# INTEGRATION-LIKE TESTS - Complete Workflows
# ============================================================================

class TestViewProjectMembersWorkflow:
    """Tests for complete workflows involving viewing project members"""

    def test_new_project_shows_only_owner_initially(self):
        """Test that a newly created project shows only the owner as a member"""
        # Arrange
        project_id = "21212121-2121-2121-2121-212121212121"
        owner_id = "22222222-2222-2222-2222-222222222222"
        
        mock_result = Mock()
        mock_result.data = [
            {
                "project_id": project_id,
                "user_id": owner_id,
                "role": "owner",
                "users": {"email": "newowner@test.com", "display_name": "New Project Owner"}
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            members = ProjectService.get_project_members(project_id)
        
        # Assert
        assert len(members) == 1
        assert members[0]["role"] == "owner"
        assert members[0]["user_id"] == owner_id

    def test_member_list_reflects_added_collaborators(self):
        """Test that member list correctly shows newly added collaborators"""
        # Arrange
        project_id = "23232323-2323-2323-2323-232323232323"
        
        # Initial state: only owner
        mock_result_initial = Mock()
        mock_result_initial.data = [
            {
                "project_id": project_id,
                "user_id": "owner1",
                "role": "owner",
                "users": {"email": "owner@test.com", "display_name": "Owner"}
            }
        ]
        
        # After adding members
        mock_result_after = Mock()
        mock_result_after.data = [
            {
                "project_id": project_id,
                "user_id": "owner1",
                "role": "owner",
                "users": {"email": "owner@test.com", "display_name": "Owner"}
            },
            {
                "project_id": project_id,
                "user_id": "staff1",
                "role": "staff",
                "users": {"email": "staff1@test.com", "display_name": "New Staff"}
            },
            {
                "project_id": project_id,
                "user_id": "staff2",
                "role": "staff",
                "users": {"email": "staff2@test.com", "display_name": "Another Staff"}
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            
            # First call returns initial state
            mock_eq.execute.return_value = mock_result_initial
            initial_members = ProjectService.get_project_members(project_id)
            
            # Second call returns state after adding members
            mock_eq.execute.return_value = mock_result_after
            updated_members = ProjectService.get_project_members(project_id)
        
        # Assert
        assert len(initial_members) == 1
        assert len(updated_members) == 3
        assert updated_members[1]["role"] == "staff"
        assert updated_members[2]["role"] == "staff"

    def test_all_members_can_see_complete_collaborator_list(self):
        """Test that all project members can see the complete list of collaborators"""
        # Arrange
        project_id = "24242424-2424-2424-2424-242424242424"
        owner_id = "owner123"
        manager_id = "manager456"
        staff_id = "staff789"
        
        mock_result = Mock()
        mock_result.data = [
            {
                "project_id": project_id,
                "user_id": owner_id,
                "role": "owner",
                "users": {"email": "owner@test.com", "display_name": "Owner"}
            },
            {
                "project_id": project_id,
                "user_id": manager_id,
                "role": "manager",
                "users": {"email": "manager@test.com", "display_name": "Manager"}
            },
            {
                "project_id": project_id,
                "user_id": staff_id,
                "role": "staff",
                "users": {"email": "staff@test.com", "display_name": "Staff"}
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.select') as mock_select, \
             patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select_chain = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select_chain
            mock_select_chain.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # All three users should see same member list
            for user_id in [owner_id, manager_id, staff_id]:
                # Mock is_project_member
                mock_select.return_value = [
                    {"project_id": project_id, "user_id": user_id, "role": "owner"}
                ]
                
                is_member = ProjectService.is_project_member(project_id, user_id)
                members = ProjectService.get_project_members(project_id)
                
                # Assert
                assert is_member is True
                assert len(members) == 3


# ============================================================================
# DATA VALIDATION TESTS - Response Format and Structure
# ============================================================================

class TestViewProjectMembersDataValidation:
    """Tests for data validation and response structure"""

    def test_member_response_has_correct_structure(self):
        """Test that each member object has the correct structure matching ProjectMemberOut model"""
        # Arrange
        project_id = "25252525-2525-2525-2525-252525252525"
        
        mock_result = Mock()
        mock_result.data = [
            {
                "project_id": project_id,
                "user_id": "user123",
                "role": "staff",
                "users": {"email": "user@test.com", "display_name": "Test User"}
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            result = ProjectService.get_project_members(project_id)
        
        # Assert
        member = result[0]
        # Check all required fields from ProjectMemberOut model
        assert isinstance(member, dict)
        assert "project_id" in member
        assert "user_id" in member
        assert "role" in member
        assert "user_email" in member
        assert "user_display_name" in member
        
        # Check field types
        assert isinstance(member["project_id"], str)
        assert isinstance(member["user_id"], str)
        assert isinstance(member["role"], str)
        assert isinstance(member["user_email"], str) or member["user_email"] is None
        assert isinstance(member["user_display_name"], str) or member["user_display_name"] is None

    def test_role_values_are_valid(self):
        """Test that role values are from the expected set (owner, manager, staff)"""
        # Arrange
        project_id = "26262626-2626-2626-2626-262626262626"
        valid_roles = {"owner", "manager", "staff"}
        
        mock_result = Mock()
        mock_result.data = [
            {
                "project_id": project_id,
                "user_id": "user1",
                "role": "owner",
                "users": {"email": "owner@test.com", "display_name": "Owner"}
            },
            {
                "project_id": project_id,
                "user_id": "user2",
                "role": "manager",
                "users": {"email": "manager@test.com", "display_name": "Manager"}
            },
            {
                "project_id": project_id,
                "user_id": "user3",
                "role": "staff",
                "users": {"email": "staff@test.com", "display_name": "Staff"}
            }
        ]
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            result = ProjectService.get_project_members(project_id)
        
        # Assert
        for member in result:
            assert member["role"] in valid_roles

    def test_empty_project_returns_empty_list_not_none(self):
        """Test that empty projects return an empty list [], not None"""
        # Arrange
        project_id = "27272727-2727-2727-2727-272727272727"
        
        mock_result = Mock()
        mock_result.data = []
        
        with patch('app.services.supabase_service.SupabaseService.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            
            mock_get_client.return_value = mock_client
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_result
            
            # Act
            result = ProjectService.get_project_members(project_id)
        
        # Assert
        assert result is not None
        assert result == []
        assert isinstance(result, list)
