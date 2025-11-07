"use client";

import { useState, useEffect } from "react";
import { ProjectsAPI, UsersAPI, ProjectMember, User } from "@/lib/api";
import DeleteConfirmationDialog from "@/components/DeleteConfirmationDialog";
import {
  Search,
  Plus,
  X,
  User as UserIcon,
  Crown,
  Shield,
  Users,
  Archive,
} from "lucide-react";

interface ProjectMemberManagerProps {
  projectId: string;
  projectName: string;
  onClose: () => void;
}

export default function ProjectMemberManager({
  projectId,
  projectName,
  onClose,
}: ProjectMemberManagerProps) {
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [showAddMember, setShowAddMember] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const selectedRole = "staff"; // Always assign staff role
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [deleteDialog, setDeleteDialog] = useState<{
    isOpen: boolean;
    member: ProjectMember | null;
  }>({ isOpen: false, member: null });

  // Load project members
  const loadMembers = async () => {
    try {
      const data = await ProjectsAPI.getMembers(projectId);
      setMembers(data);
    } catch {
      setError("Failed to load project members");
    }
  };

  // Search users
  const searchUsers = async (query: string) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      const data = await UsersAPI.search(query);
      // Filter out users who are already members
      const existingMemberIds = members.map((m) => m.user_id);
      const filteredData = data.filter(
        (user) => !existingMemberIds.includes(user.id)
      );
      setSearchResults(filteredData);
    } catch {
      setError("Failed to search users");
    }
  };

  // Add member to project
  const addMember = async () => {
    if (!selectedUser) return;

    setLoading(true);
    try {
      await ProjectsAPI.addMember(projectId, selectedUser.email, selectedRole);
      await loadMembers();
      setSelectedUser(null);
      // selectedRole is always "staff", no need to reset
      setShowAddMember(false);
      setSearchQuery("");
      setSearchResults([]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add member");
    } finally {
      setLoading(false);
    }
  };

  // Update member role
  const updateMemberRole = async (memberId: string, newRole: string) => {
    try {
      setLoading(true);
      await ProjectsAPI.updateMemberRole(projectId, memberId, newRole);
      await loadMembers(); // Reload members
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update member role");
    } finally {
      setLoading(false);
    }
  };

  // Show delete dialog
  const showDeleteDialog = (member: ProjectMember) => {
    setDeleteDialog({ isOpen: true, member });
  };

  // Confirm remove member
  const confirmRemoveMember = async () => {
    if (!deleteDialog.member) return;

    try {
      setLoading(true);
      await ProjectsAPI.removeMember(projectId, deleteDialog.member.user_id);
      await loadMembers();
      setDeleteDialog({ isOpen: false, member: null });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to remove member");
    } finally {
      setLoading(false);
    }
  };

  // Close delete dialog
  const closeDeleteDialog = () => {
    setDeleteDialog({ isOpen: false, member: null });
  };

  // Get role icon
  const getRoleIcon = (role: string) => {
    switch (role) {
      case "owner":
        return <Crown className="h-4 w-4 text-yellow-500" />;
      case "manager":
        return <Shield className="h-4 w-4 text-blue-500" />;
      case "staff":
        return <UserIcon className="h-4 w-4 text-green-500" />;
      default:
        return <Users className="h-4 w-4 text-gray-500" />;
    }
  };

  // Get role color
  const getRoleColor = (role: string) => {
    switch (role) {
      case "owner":
        return "bg-yellow-100 text-yellow-800";
      case "manager":
        return "bg-blue-100 text-blue-800";
      case "staff":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  useEffect(() => {
    loadMembers();
  }, [projectId]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      searchUsers(searchQuery);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, members]);

  return (
    <div className="fixed inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">{projectName} - Members</h2>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-gray-100 rounded-md"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mx-4 mt-3 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
            {error}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {/* Add Member Section */}
          <div className="mb-4">
            <button
              onClick={() => setShowAddMember(!showAddMember)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
            >
              <Plus className="h-4 w-4" />
              Add Member
            </button>

            {showAddMember && (
              <div className="mt-3 p-3 border rounded-md bg-gray-50">
                <div className="mb-3">
                  <label className="block text-sm font-medium mb-1.5">
                    Search Users
                  </label>
                  <div className="relative">
                    <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search by email or name..."
                      className="w-full pl-9 pr-3 py-2 border rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    />
                  </div>
                </div>

                {searchResults.length > 0 && (
                  <div className="mb-3">
                    <label className="block text-sm font-medium mb-1.5">
                      Select User
                    </label>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {searchResults.map((user) => (
                        <div
                          key={user.id}
                          onClick={() => setSelectedUser(user)}
                          className={`p-2 border rounded-md cursor-pointer hover:bg-gray-100 ${
                            selectedUser?.id === user.id
                              ? "bg-blue-50 border-blue-300"
                              : ""
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <UserIcon className="h-4 w-4 text-gray-400" />
                            <div>
                              <p className="font-medium text-sm">
                                {user.display_name || user.email}
                              </p>
                              <p className="text-xs text-gray-500">
                                {user.email}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedUser && (
                  <div className="flex gap-2">
                    <button
                      onClick={addMember}
                      disabled={loading}
                      className="px-3 py-1.5 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 text-sm"
                    >
                      {loading ? "Adding..." : "Add Member"}
                    </button>
                    <button
                      onClick={() => {
                        setSelectedUser(null);
                        setSearchQuery("");
                        setSearchResults([]);
                      }}
                      className="px-3 py-1.5 bg-gray-500 text-white rounded-md hover:bg-gray-600 text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Current Members */}
          <div>
            <h3 className="text-sm font-medium mb-3 text-gray-700">
              Current Members
            </h3>
            <div className="space-y-2">
              {members.map((member) => (
                <div
                  key={member.user_id}
                  className="flex items-center justify-between p-3 border rounded-md"
                >
                  <div className="flex items-center gap-2">
                    <UserIcon className="h-4 w-4 text-gray-400" />
                    <div>
                      <p className="font-medium text-sm">
                        {member.user_display_name || member.user_email}
                      </p>
                      <p className="text-xs text-gray-500">
                        {member.user_email}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-1.5 py-0.5 rounded text-xs font-medium flex items-center gap-1 ${getRoleColor(
                        member.role
                      )}`}
                    >
                      {getRoleIcon(member.role)}
                      {member.role}
                    </span>
                    {member.role !== "owner" && (
                      <button
                        onClick={() => showDeleteDialog(member)}
                        className="p-1 text-red-600 hover:bg-red-50 rounded"
                        title="Remove Member"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Simple Confirmation Dialog */}
      {deleteDialog.isOpen && (
        <div className="fixed inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100">
                <X className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  Remove Member
                </h3>
                <p className="text-sm text-gray-500">
                  Are you sure you want to remove this member from the project?
                </p>
              </div>
            </div>

            <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
              <p className="text-sm text-red-800">
                <strong>
                  {deleteDialog.member?.user_display_name ||
                    deleteDialog.member?.user_email}
                </strong>{" "}
                will be removed from the project.
              </p>
            </div>

            <div className="flex gap-3 justify-end">
              <button
                onClick={closeDeleteDialog}
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmRemoveMember}
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                {loading ? "Removing..." : "Remove Member"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
