"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { TeamsAPI, Team, TeamMember, UsersAPI, User } from "@/lib/api";
import {
  isAdmin,
  hasManagerRole,
  canAdminManage,
  isStaff,
} from "@/utils/role-utils";
import {
  Plus,
  Users,
  Search,
  Filter,
  Edit,
  Trash2,
  UserPlus,
  UserMinus,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function TeamsPage() {
  const { user } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [allTeams, setAllTeams] = useState<Team[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // UI States
  const [showCreateTeam, setShowCreateTeam] = useState(false);
  const [showAllTeams, setShowAllTeams] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);

  // Form States
  const [teamName, setTeamName] = useState("");
  const [teamDescription, setTeamDescription] = useState("");
  const [selectedUserId, setSelectedUserId] = useState("");
  const [memberRole, setMemberRole] = useState<"member" | "manager">("member");
  const [selectedMembers, setSelectedMembers] = useState<string[]>([]);

  // Team member management states
  const [editingMembers, setEditingMembers] = useState(false);
  const [membersToAdd, setMembersToAdd] = useState<string[]>([]);
  const [membersToRemove, setMembersToRemove] = useState<string[]>([]);

  // Load teams based on user role
  const loadTeams = async () => {
    try {
      setLoading(true);
      if (isAdmin(user)) {
        // Admin can see all teams by default
        const allTeamsData = await TeamsAPI.listAll();
        setAllTeams(allTeamsData);
        setTeams(allTeamsData); // Show all teams by default for admin
        setShowAllTeams(true); // Set to true by default for admin
      } else {
        // Non-admin users see their teams
        const teamsData = await TeamsAPI.list();
        setTeams(teamsData);
        setShowAllTeams(false); // Set to false for non-admin users
      }
    } catch (e: any) {
      setError("Failed to load teams");
    } finally {
      setLoading(false);
    }
  };

  // Load users for adding to teams
  const loadUsers = async () => {
    try {
      const usersData = await UsersAPI.list();
      setUsers(usersData);
    } catch (e: any) {
      console.error("Failed to load users:", e);
    }
  };

  // Load team members
  const loadTeamMembers = async (teamId: string) => {
    try {
      const members = await TeamsAPI.getMembers(teamId);
      setTeamMembers(members);
      // Reset editing state when loading new team
      setEditingMembers(false);
      setMembersToAdd([]);
      setMembersToRemove([]);
    } catch (e: any) {
      console.error("Failed to load team members:", e);
    }
  };

  useEffect(() => {
    loadTeams();
    loadUsers();
  }, []);

  // Load team members when a team is selected
  useEffect(() => {
    if (selectedTeam) {
      loadTeamMembers(selectedTeam.id);
    }
  }, [selectedTeam]);

  // Helper functions for member selection
  const addSelectedMember = (userId: string) => {
    if (!selectedMembers.includes(userId)) {
      setSelectedMembers([...selectedMembers, userId]);
    }
  };

  const removeSelectedMember = (userId: string) => {
    setSelectedMembers(selectedMembers.filter((id) => id !== userId));
  };

  const getSelectedMemberNames = () => {
    return selectedMembers.map((userId) => {
      const user = users.find((u) => u.id === userId);
      return user ? user.display_name || user.email : userId;
    });
  };

  // Helper functions for bulk member management
  const addMemberToAddList = (userId: string) => {
    if (!membersToAdd.includes(userId)) {
      setMembersToAdd([...membersToAdd, userId]);
    }
  };

  const removeMemberFromAddList = (userId: string) => {
    setMembersToAdd(membersToAdd.filter((id) => id !== userId));
  };

  const addMemberToRemoveList = (userId: string) => {
    if (!membersToRemove.includes(userId)) {
      setMembersToRemove([...membersToRemove, userId]);
    }
  };

  const removeMemberFromRemoveList = (userId: string) => {
    setMembersToRemove(membersToRemove.filter((id) => id !== userId));
  };

  const saveMemberChanges = async () => {
    try {
      // Add new members
      for (const memberId of membersToAdd) {
        await TeamsAPI.addMember(selectedTeam!.id, memberId, "member");
      }

      // Remove members
      for (const memberId of membersToRemove) {
        await TeamsAPI.removeMember(selectedTeam!.id, memberId);
      }

      // Reset states
      setMembersToAdd([]);
      setMembersToRemove([]);
      setEditingMembers(false);

      // Reload team members
      await loadTeamMembers(selectedTeam!.id);
    } catch (e: any) {
      setError(e.message || "Failed to update team members");
    }
  };

  const cancelMemberEditing = () => {
    setMembersToAdd([]);
    setMembersToRemove([]);
    setEditingMembers(false);
  };

  // Create team
  const createTeam = async () => {
    if (!teamName.trim()) {
      setError("Team name is required");
      return;
    }

    try {
      // Create the team first
      const newTeam = await TeamsAPI.create(teamName, teamDescription);

      // Add selected members to the team
      for (const memberId of selectedMembers) {
        try {
          await TeamsAPI.addMember(newTeam.id, memberId, "member");
        } catch (e) {
          console.error(`Failed to add member ${memberId}:`, e);
        }
      }

      // Reset form
      setTeamName("");
      setTeamDescription("");
      setSelectedMembers([]);
      setShowCreateTeam(false);
      await loadTeams();
    } catch (e: any) {
      setError(e.message || "Failed to create team");
    }
  };

  // Delete team
  const deleteTeam = async (teamId: string) => {
    if (!confirm("Are you sure you want to delete this team?")) return;

    try {
      await TeamsAPI.delete(teamId);
      await loadTeams();
    } catch (e: any) {
      setError(e.message || "Failed to delete team");
    }
  };

  // Add member to team
  const addMember = async (teamId: string) => {
    if (!selectedUserId) {
      setError("Please select a user");
      return;
    }

    try {
      await TeamsAPI.addMember(teamId, selectedUserId, memberRole);
      setSelectedUserId("");
      setMemberRole("member");
      await loadTeamMembers(teamId);
    } catch (e: any) {
      setError(e.message || "Failed to add member");
    }
  };

  // Remove member from team
  const removeMember = async (teamId: string, userId: string) => {
    if (!confirm("Are you sure you want to remove this member?")) return;

    try {
      await TeamsAPI.removeMember(teamId, userId);
      await loadTeamMembers(teamId);
    } catch (e: any) {
      setError(e.message || "Failed to remove member");
    }
  };

  // Get filtered teams
  const getFilteredTeams = () => {
    if (isAdmin(user)) {
      // Admin can toggle between all teams and their teams
      const teamsToShow = showAllTeams ? allTeams : teams;
      return teamsToShow.filter((team) =>
        team.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    } else {
      // Non-admin users only see their teams
      return teams.filter((team) =>
        team.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
  };

  // Check if user can manage team
  const canManageTeam = (team: Team) => {
    if (!user) return false;

    // Admin alone is read-only
    if (isAdmin(user) && !hasManagerRole(user) && !isStaff(user)) {
      return false;
    }

    // Manager can manage teams they created (regardless of admin status)
    if (hasManagerRole(user) && team.manager_id === user.id) {
      return true;
    }

    // Staff can manage teams they are members of (regardless of admin status)
    if (isStaff(user)) {
      const userMembership = teamMembers.find(
        (member) => member.user_id === user.id
      );
      return !!userMembership;
    }

    return false;
  };

  // Check if user can view team details
  const canViewTeam = (team: Team) => {
    if (!user) return false;

    // Admin can view all teams
    if (isAdmin(user)) {
      return true;
    }

    // Manager can view teams they created
    if (hasManagerRole(user) && team.manager_id === user.id) {
      return true;
    }

    // Staff can view teams they are members of
    if (isStaff(user)) {
      const userMembership = teamMembers.find(
        (member) => member.user_id === user.id
      );
      return !!userMembership;
    }

    return false;
  };

  // Get users that can be added to team based on current user's role
  const getAddableUsers = () => {
    if (!user) return [];

    return users.filter((targetUser) => {
      // Don't show current user
      if (targetUser.id === user.id) return false;

      // Manager can add staff, users, and admins
      if (hasManagerRole(user)) {
        return true;
      }

      // Staff can only add other staff (not managers or admins)
      if (isStaff(user)) {
        return (
          isStaff(targetUser) &&
          !hasManagerRole(targetUser) &&
          !isAdmin(targetUser)
        );
      }

      return false;
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Teams</h1>
          <p className="text-muted-foreground">
            Manage your teams and team members
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Admin Toggle */}
          {isAdmin(user) && (
            <Button
              variant={showAllTeams ? "default" : "outline"}
              size="sm"
              onClick={() => {
                if (showAllTeams) {
                  // Switch to my teams
                  setShowAllTeams(false);
                  TeamsAPI.list().then(setTeams);
                } else {
                  // Switch to all teams
                  setShowAllTeams(true);
                  setTeams(allTeams);
                }
              }}
            >
              {showAllTeams ? "My Teams" : "All Teams"}
            </Button>
          )}

          {/* Create Team Button */}
          {hasManagerRole(user) && (
            <Button
              onClick={() => setShowCreateTeam(true)}
              size="sm"
              className="flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              New Team
            </Button>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
          {error}
        </div>
      )}

      {/* Admin Filtering */}
      {isAdmin(user) && showAllTeams && (
        <div className="p-4 border bg-card rounded-lg">
          <div className="flex gap-3">
            <div className="flex-1">
              <Input
                placeholder="Search teams..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full"
              />
            </div>
          </div>
        </div>
      )}

      {/* Create Team Form */}
      {showCreateTeam && hasManagerRole(user) && (
        <div className="p-4 border bg-card rounded-lg">
          <h3 className="text-lg font-semibold mb-4">Create New Team</h3>
          <div className="space-y-4">
            <div>
              <Label htmlFor="teamName">Team Name</Label>
              <Input
                id="teamName"
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                placeholder="Enter team name"
              />
            </div>
            <div>
              <Label htmlFor="teamDescription">Description (Optional)</Label>
              <Input
                id="teamDescription"
                value={teamDescription}
                onChange={(e) => setTeamDescription(e.target.value)}
                placeholder="Enter team description"
              />
            </div>

            {/* Member Selection */}
            <div>
              <Label>Add Members (Optional)</Label>
              <div className="space-y-3">
                {/* Add Member Dropdown */}
                <div className="flex gap-2">
                  <Select
                    value={selectedUserId}
                    onValueChange={(value) => {
                      setSelectedUserId(value);
                      addSelectedMember(value);
                      setSelectedUserId(""); // Reset selection
                    }}
                  >
                    <SelectTrigger className="flex-1">
                      <SelectValue placeholder="Select a user to add" />
                    </SelectTrigger>
                    <SelectContent>
                      {getAddableUsers()
                        .filter((user) => !selectedMembers.includes(user.id))
                        .map((user) => (
                          <SelectItem key={user.id} value={user.id}>
                            {user.display_name || user.email}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Selected Members Display */}
                {selectedMembers.length > 0 && (
                  <div className="space-y-2">
                    <Label className="text-sm text-muted-foreground">
                      Selected Members:
                    </Label>
                    <div className="flex flex-wrap gap-2">
                      {getSelectedMemberNames().map((name, index) => (
                        <div
                          key={selectedMembers[index]}
                          className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-sm"
                        >
                          <span>{name}</span>
                          <button
                            type="button"
                            onClick={() =>
                              removeSelectedMember(selectedMembers[index])
                            }
                            className="text-blue-600 hover:text-blue-800"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={createTeam}>Create Team</Button>
              <Button
                variant="outline"
                onClick={() => {
                  setShowCreateTeam(false);
                  setTeamName("");
                  setTeamDescription("");
                  setSelectedMembers([]);
                  setError("");
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Teams List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {getFilteredTeams().map((team) => (
          <div key={team.id} className="border bg-card rounded-lg p-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-lg">{team.name}</h3>
                {team.description && (
                  <p className="text-sm text-muted-foreground mt-1">
                    {team.description}
                  </p>
                )}
              </div>
              {(canManageTeam(team) || canViewTeam(team)) && (
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedTeam(team)}
                    title={canManageTeam(team) ? "Manage team" : "View team"}
                  >
                    <Users className="h-4 w-4" />
                  </Button>
                  {canManageTeam(team) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteTeam(team.id)}
                      title="Delete team"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              )}
            </div>

            <div className="text-xs text-muted-foreground">
              Created: {new Date(team.created_at).toLocaleDateString()}
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {getFilteredTeams().length === 0 && (
        <div className="text-center py-8">
          <Users className="h-8 w-8 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-500 text-sm mb-1">
            {isAdmin(user) && showAllTeams ? "No teams found" : "No teams yet"}
          </p>
          <p className="text-gray-400 text-xs">
            {isAdmin(user) && showAllTeams
              ? "Try adjusting your search"
              : hasManagerRole(user)
              ? "Create your first team"
              : "Ask your manager to add you to a team"}
          </p>
        </div>
      )}

      {/* Team Members Modal */}
      {selectedTeam && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-background rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">
                {selectedTeam.name} - Members
              </h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedTeam(null)}
              >
                ×
              </Button>
            </div>

            {/* Member Management */}
            {canManageTeam(selectedTeam) && (
              <div className="border-b pb-4 mb-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium">Manage Members</h3>
                  {!editingMembers ? (
                    <Button
                      onClick={() => setEditingMembers(true)}
                      size="sm"
                      variant="outline"
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Edit Members
                    </Button>
                  ) : (
                    <div className="flex gap-2">
                      <Button
                        onClick={saveMemberChanges}
                        size="sm"
                        disabled={
                          membersToAdd.length === 0 &&
                          membersToRemove.length === 0
                        }
                      >
                        Save Changes
                      </Button>
                      <Button
                        onClick={cancelMemberEditing}
                        size="sm"
                        variant="outline"
                      >
                        Cancel
                      </Button>
                    </div>
                  )}
                </div>

                {editingMembers && (
                  <div className="space-y-4">
                    {/* Add Members Section */}
                    <div>
                      <Label className="text-sm font-medium">Add Members</Label>
                      <p className="text-xs text-muted-foreground mb-2">
                        Select users to add to the team. Current members are not
                        shown.
                      </p>
                      <div className="mt-2">
                        <Select
                          value=""
                          onValueChange={(value) => {
                            addMemberToAddList(value);
                          }}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select users to add..." />
                          </SelectTrigger>
                          <SelectContent>
                            {getAddableUsers()
                              .filter(
                                (user) =>
                                  !teamMembers.some(
                                    (member) => member.user_id === user.id
                                  ) && !membersToAdd.includes(user.id)
                              )
                              .map((user) => (
                                <SelectItem key={user.id} value={user.id}>
                                  {user.display_name || user.email}
                                </SelectItem>
                              ))}
                          </SelectContent>
                        </Select>
                      </div>
                      {getAddableUsers().filter(
                        (user) =>
                          !teamMembers.some(
                            (member) => member.user_id === user.id
                          ) && !membersToAdd.includes(user.id)
                      ).length === 0 && (
                        <p className="text-xs text-muted-foreground mt-2">
                          All available users are already in this team.
                        </p>
                      )}
                      {membersToAdd.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-2">
                          {membersToAdd.map((userId) => {
                            const user = users.find((u) => u.id === userId);
                            return (
                              <div
                                key={userId}
                                className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 rounded-md text-sm"
                              >
                                <span>
                                  {user?.display_name || user?.email || userId}
                                </span>
                                <button
                                  type="button"
                                  onClick={() =>
                                    removeMemberFromAddList(userId)
                                  }
                                  className="text-green-600 hover:text-green-800"
                                >
                                  <X className="h-3 w-3" />
                                </button>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    {/* Remove Members Section */}
                    <div>
                      <Label className="text-sm font-medium">
                        Remove Members
                      </Label>
                      <p className="text-xs text-muted-foreground mb-2">
                        Click on members below to mark them for removal.
                      </p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {teamMembers.map((member) => {
                          const memberUser = users.find(
                            (u) => u.id === member.user_id
                          );
                          const isMarkedForRemoval = membersToRemove.includes(
                            member.user_id
                          );

                          return (
                            <div
                              key={member.user_id}
                              className={`flex items-center gap-1 px-2 py-1 rounded-md text-sm cursor-pointer transition-colors ${
                                isMarkedForRemoval
                                  ? "bg-red-100 text-red-800 border border-red-200"
                                  : "bg-gray-100 text-gray-800 hover:bg-red-50 border border-gray-200"
                              }`}
                              onClick={() => {
                                if (isMarkedForRemoval) {
                                  removeMemberFromRemoveList(member.user_id);
                                } else {
                                  addMemberToRemoveList(member.user_id);
                                }
                              }}
                            >
                              <span>
                                {memberUser?.display_name ||
                                  memberUser?.email ||
                                  member.user_id}
                              </span>
                              <span className="text-xs">({member.role})</span>
                              {isMarkedForRemoval && <X className="h-3 w-3" />}
                            </div>
                          );
                        })}
                      </div>
                      {teamMembers.length === 0 && (
                        <p className="text-xs text-muted-foreground mt-2">
                          No members to remove.
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Team Info for View-Only Users */}
            {!canManageTeam(selectedTeam) && canViewTeam(selectedTeam) && (
              <div className="border-b pb-4 mb-4">
                <h3 className="font-medium mb-3">Team Information</h3>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">Manager:</span>
                    <span className="text-sm text-muted-foreground">
                      {users.find((u) => u.id === selectedTeam.manager_id)
                        ?.display_name ||
                        users.find((u) => u.id === selectedTeam.manager_id)
                          ?.email ||
                        "Unknown"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">Members:</span>
                    <span className="text-sm text-muted-foreground">
                      {teamMembers.length} member
                      {teamMembers.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Current Members Section */}
            <div>
              <h3 className="font-medium mb-3 flex items-center gap-2">
                <Users className="h-4 w-4" />
                Current Members ({teamMembers.length})
              </h3>
              <div className="space-y-2">
                {teamMembers.map((member) => {
                  const memberUser = users.find((u) => u.id === member.user_id);
                  const isMarkedForRemoval = membersToRemove.includes(
                    member.user_id
                  );

                  return (
                    <div
                      key={member.id}
                      className={`flex items-center justify-between p-3 border rounded-lg transition-colors ${
                        isMarkedForRemoval
                          ? "bg-red-50 border-red-200"
                          : "bg-gray-50 border-gray-200"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-blue-600">
                            {(memberUser?.display_name ||
                              memberUser?.email ||
                              "U")[0].toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <div className="font-medium">
                            {memberUser?.display_name ||
                              memberUser?.email ||
                              "Unknown User"}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {member.role === "manager" ? (
                              <span className="text-blue-600 font-medium">
                                Team Manager
                              </span>
                            ) : (
                              <span>Member</span>
                            )}{" "}
                            • Joined{" "}
                            {new Date(member.joined_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                      {canManageTeam(selectedTeam) &&
                        member.role !== "manager" &&
                        !editingMembers && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              removeMember(selectedTeam.id, member.user_id)
                            }
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <UserMinus className="h-4 w-4" />
                          </Button>
                        )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
