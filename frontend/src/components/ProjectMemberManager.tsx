"use client";

import { useState, useEffect } from "react";
import { ProjectsAPI, UsersAPI, ProjectMember, User } from "@/lib/api";
import {
  Search,
  Plus,
  X,
  User as UserIcon,
  Crown,
  Shield,
  Users,
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

  // Load project members
  const loadMembers = async () => {
    try {
      const data = await ProjectsAPI.getMembers(projectId);
      setMembers(data);
    } catch (err: any) {
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
    } catch (err: any) {
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
    } catch (err: any) {
      setError(err.message || "Failed to add member");
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
    } catch (err: any) {
      setError(err.message || "Failed to update member role");
    } finally {
      setLoading(false);
    }
  };

  // Remove member from project
  const removeMember = async (memberId: string) => {
    if (!confirm("Are you sure you want to remove this member?")) return;

    try {
      await ProjectsAPI.removeMember(projectId, memberId);
      await loadMembers();
    } catch (err: any) {
      setError(err.message || "Failed to remove member");
    }
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">
            Manage Members - {projectName}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Add Member Section */}
        <div className="mb-6">
          <button
            onClick={() => setShowAddMember(!showAddMember)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            Add Member
          </button>

          {showAddMember && (
            <div className="mt-4 p-4 border rounded-lg bg-gray-50">
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  Search Users
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by email or name..."
                    className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {searchResults.length > 0 && (
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">
                    Select User
                  </label>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {searchResults.map((user) => (
                      <div
                        key={user.id}
                        onClick={() => setSelectedUser(user)}
                        className={`p-3 border rounded-lg cursor-pointer hover:bg-gray-100 ${
                          selectedUser?.id === user.id
                            ? "bg-blue-50 border-blue-300"
                            : ""
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <UserIcon className="h-5 w-5 text-gray-400" />
                          <div>
                            <p className="font-medium">
                              {user.display_name || user.email}
                            </p>
                            <p className="text-sm text-gray-500">
                              {user.email}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedUser && <div className="mb-4"></div>}

              {selectedUser && (
                <div className="flex gap-2">
                  <button
                    onClick={addMember}
                    disabled={loading}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                  >
                    {loading ? "Adding..." : "Add Member"}
                  </button>
                  <button
                    onClick={() => {
                      setSelectedUser(null);
                      setSearchQuery("");
                      setSearchResults([]);
                    }}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Members List */}
        <div>
          <h3 className="text-lg font-medium mb-4">
            Project Members ({members.length})
          </h3>
          <div className="space-y-3">
            {members.map((member) => (
              <div
                key={member.user_id}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <UserIcon className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="font-medium">
                      {member.user_display_name || member.user_email}
                    </p>
                    <p className="text-sm text-gray-500">{member.user_email}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${getRoleColor(
                      member.role
                    )}`}
                  >
                    {getRoleIcon(member.role)}
                    {member.role}
                  </span>
                  {member.role !== "owner" && (
                    <button
                      onClick={() => removeMember(member.user_id)}
                      className="p-1 text-red-600 hover:bg-red-50 rounded"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
