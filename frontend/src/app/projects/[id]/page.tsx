"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import {
  ProjectsAPI,
  TasksAPI,
  Project,
  Task,
  UsersAPI,
  User,
  ProjectMember,
} from "@/lib/api";
import AssigneeSelector from "@/components/AssigneeSelector";
import CreateTaskModal, { TaskFormData } from "@/components/CreateTaskModal";
import ProjectDetailSkeleton from "@/components/ProjectDetailSkeleton";
import TaskListSkeleton from "@/components/TaskListSkeleton";
import { isAdmin, isManager, canAdminManage } from "@/utils/role-utils";
import {
  ArrowLeft,
  Plus,
  Clock,
  User as UserIcon,
  Calendar,
  MoreVertical,
  Edit,
  Trash2,
  AlertCircle,
  Search,
  Filter,
  X,
  Tag,
  ChevronDown,
  ChevronRight,
  Archive,
  Flag,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [error, setError] = useState("");
  const [showCreateTaskModal, setShowCreateTaskModal] = useState(false);
  const [creatingTask, setCreatingTask] = useState(false);
  const [editingAssignees, setEditingAssignees] = useState<string | null>(null);
  const [tempAssigneeIds, setTempAssigneeIds] = useState<string[]>([]);

  // Filter states
  const [showFilters, setShowFilters] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [assigneeFilter, setAssigneeFilter] = useState<string>("all");
  const [dateFilter, setDateFilter] = useState<string>("all");
  const [tagFilter, setTagFilter] = useState<string>("all");
  const [priorityFilter, setPriorityFilter] = useState<string>("all");

  // Project members visibility state
  const [showProjectMembers, setShowProjectMembers] = useState(false);

  // Confirmation dialog state
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean;
    title: string;
    description: string;
    onConfirm: () => void;
    variant?: "default" | "destructive";
  }>({
    isOpen: false,
    title: "",
    description: "",
    onConfirm: () => {},
    variant: "default",
  });

  // Load project details
  const loadProject = async () => {
    try {
      // Try to get project directly by ID first (works for admins and members)
      try {
        const projectData = await ProjectsAPI.getById(projectId);
        setProject(projectData);
        return;
      } catch (err) {
        // If direct access fails, try loading from user's projects
        console.log("Direct project access failed, trying user projects");
      }

      // Fallback: load user's projects and find the one with matching ID
      const projects = await ProjectsAPI.list();
      const foundProject = projects.find((p) => p.id === projectId);
      if (foundProject) {
        setProject(foundProject);
      } else {
        setError("Project not found");
      }
    } catch (err: any) {
      setError("Failed to load project");
    }
  };

  // Load tasks for this project
  const loadTasks = async () => {
    try {
      setLoadingTasks(true);
      const projectTasks = await TasksAPI.list(projectId);
      setTasks(projectTasks);
    } catch (err: any) {
      console.error("Failed to load tasks:", err);
      // If tasks endpoint doesn't exist yet, use empty array
      setTasks([]);
    } finally {
      setLoadingTasks(false);
    }
  };

  // Load project members for task assignment
  const loadProjectMembers = async () => {
    try {
      const projectMembers = await ProjectsAPI.getMembers(projectId);
      // Convert project members to user format for the assignee selector
      const memberUsers: User[] = projectMembers.map((member) => ({
        id: member.user_id,
        email: member.user_email || "",
        display_name: member.user_display_name || undefined,
        roles: [member.role], // Include the actual project role from database
      }));

      // Ensure the current user (project owner) is always included in assignee options
      if (user && project && user.id === project.owner_id) {
        const currentUserExists = memberUsers.some(
          (member) => member.id === user.id
        );
        if (!currentUserExists) {
          memberUsers.unshift({
            id: user.id,
            email: user.email,
            display_name: user.full_name || undefined,
            roles: user.roles || [],
          });
        }
      }

      setUsers(memberUsers);
    } catch (err: any) {
      // Silently handle "User not found" errors - this can happen if the user exists in auth but not in users table
      const errorMessage = err?.message || String(err);
      let errorDetail = "";
      try {
        // Try to parse JSON error response
        const parsed = JSON.parse(errorMessage);
        errorDetail = parsed.detail || "";
      } catch {
        // Not JSON, use the message as-is
        errorDetail = errorMessage;
      }
      
      if (errorDetail.includes("User not found") || errorMessage.includes("User not found")) {
        // Fallback: if project members fail to load, at least include the current user if they're the owner
        if (user && project && user.id === project.owner_id) {
          setUsers([
            {
              id: user.id,
              email: user.email,
              display_name: user.full_name || undefined,
              roles: user.roles || [],
            },
          ]);
        }
        return;
      }
      console.error("Failed to load project members:", err);
      // Fallback: if project members fail to load, at least include the current user if they're the owner
      if (user && project && user.id === project.owner_id) {
        setUsers([
          {
            id: user.id,
            email: user.email,
            display_name: user.full_name || undefined,
            roles: user.roles || [],
          },
        ]);
      }
    }
  };

  // Create new task
  const createTask = async (taskData: TaskFormData) => {
    setCreatingTask(true);
    try {
      await TasksAPI.create(projectId, taskData);
      setShowCreateTaskModal(false);
      await loadTasks();
    } catch (err: any) {
      setError(err.message || "Failed to create task");
    } finally {
      setCreatingTask(false);
    }
  };

  // Update task status
  const updateTaskStatus = async (
    taskId: string,
    newStatus: Task["status"]
  ) => {
    try {
      await TasksAPI.update(taskId, { status: newStatus });
      await loadTasks();
    } catch (err: any) {
      setError("Failed to update task");
    }
  };

  // Archive task
  const archiveTask = async (taskId: string) => {
    try {
      await TasksAPI.archive(taskId);
      await loadTasks();
    } catch (err: any) {
      setError("Failed to archive task");
    }
  };

  // Get status color
  const getStatusColor = (status: Task["status"]) => {
    switch (status) {
      case "todo":
        return "bg-gray-100 text-gray-800";
      case "in_progress":
        return "bg-blue-100 text-blue-800";
      case "completed":
        return "bg-green-100 text-green-800";
      case "blocked":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  // Get status icon
  const getStatusIcon = (status: Task["status"]) => {
    switch (status) {
      case "todo":
        return <Clock className="h-4 w-4" />;
      case "in_progress":
        return <Clock className="h-4 w-4" />;
      case "completed":
        return <AlertCircle className="h-4 w-4" />;
      case "blocked":
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  // Get user display name
  const getUserDisplayName = (userId?: string | null) => {
    if (!userId) return "Unassigned";
    const foundUser = users.find((u) => u.id === userId);
    return foundUser?.display_name || foundUser?.email || "Unknown User";
  };

  // Helper function to check if a task is overdue
  const isTaskOverdue = (task: Task): boolean => {
    if (!task.due_date || task.status === "completed") return false;
    const dueDate = new Date(task.due_date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    dueDate.setHours(0, 0, 0, 0);
    return dueDate < today;
  };

  // Filter tasks based on current filter criteria
  const getFilteredTasks = () => {
    let filtered = [...tasks];

    // Exclude overdue tasks from main list (they're shown in the overdue section)
    filtered = filtered.filter((task) => !isTaskOverdue(task));

    // Search by name/description
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (task) =>
          task.title.toLowerCase().includes(query) ||
          (task.description && task.description.toLowerCase().includes(query))
      );
    }

    // Filter by status
    if (statusFilter !== "all") {
      filtered = filtered.filter((task) => task.status === statusFilter);
    }

    // Filter by assignee
    if (assigneeFilter !== "all") {
      if (assigneeFilter === "unassigned") {
        filtered = filtered.filter(
          (task) => !task.assignee_ids || task.assignee_ids.length === 0
        );
      } else {
        filtered = filtered.filter(
          (task) =>
            task.assignee_ids && task.assignee_ids.includes(assigneeFilter)
        );
      }
    }

    // Filter by date
    if (dateFilter !== "all") {
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

      filtered = filtered.filter((task) => {
        if (!task.due_date) return dateFilter === "no_date";

        const dueDate = new Date(task.due_date);
        const taskDate = new Date(
          dueDate.getFullYear(),
          dueDate.getMonth(),
          dueDate.getDate()
        );

        switch (dateFilter) {
          case "overdue":
            return taskDate < today && task.status !== "completed";
          case "today":
            return taskDate.getTime() === today.getTime();
          case "this_week":
            const weekStart = new Date(today);
            weekStart.setDate(today.getDate() - today.getDay());
            const weekEnd = new Date(weekStart);
            weekEnd.setDate(weekStart.getDate() + 6);
            return taskDate >= weekStart && taskDate <= weekEnd;
          case "this_month":
            return (
              dueDate.getMonth() === now.getMonth() &&
              dueDate.getFullYear() === now.getFullYear()
            );
          case "no_date":
            return !task.due_date;
          default:
            return true;
        }
      });
    }

    // Filter by tags
    if (tagFilter !== "all") {
      if (tagFilter === "no_tags") {
        filtered = filtered.filter(
          (task) => !task.tags || task.tags.length === 0
        );
      } else {
        filtered = filtered.filter(
          (task) => task.tags && task.tags.includes(tagFilter)
        );
      }
    }

    // Filter by priority
    if (priorityFilter !== "all") {
      if (priorityFilter === "no_priority") {
        filtered = filtered.filter(
          (task) => !task.priority || task.priority === undefined
        );
      } else if (priorityFilter === "highest_to_lowest") {
        // Sort by priority highest to lowest (10 to 1), tasks without priority go to end
        filtered.sort((a, b) => {
          const aPriority = a.priority ?? 0;
          const bPriority = b.priority ?? 0;
          if (aPriority === 0 && bPriority === 0) return 0;
          if (aPriority === 0) return 1;
          if (bPriority === 0) return -1;
          return bPriority - aPriority;
        });
      } else if (priorityFilter === "lowest_to_highest") {
        // Sort by priority lowest to highest (1 to 10), tasks without priority go to end
        filtered.sort((a, b) => {
          const aPriority = a.priority ?? 0;
          const bPriority = b.priority ?? 0;
          if (aPriority === 0 && bPriority === 0) return 0;
          if (aPriority === 0) return 1;
          if (bPriority === 0) return -1;
          return aPriority - bPriority;
        });
      } else {
        const priorityValue = parseInt(priorityFilter, 10);
        filtered = filtered.filter(
          (task) => task.priority === priorityValue
        );
      }
    }

    return filtered;
  };

  // Get all unique tags from tasks
  const getAllTags = () => {
    const tagSet = new Set<string>();
    tasks.forEach((task) => {
      if (task.tags) {
        task.tags.forEach((tag) => tagSet.add(tag));
      }
    });
    return Array.from(tagSet).sort();
  };

  // Clear all filters
  const clearFilters = () => {
    setSearchQuery("");
    setStatusFilter("all");
    setAssigneeFilter("all");
    setDateFilter("all");
    setTagFilter("all");
    setPriorityFilter("all");
  };

  // Check if any filters are active
  const hasActiveFilters = () => {
    return (
      searchQuery.trim() !== "" ||
      statusFilter !== "all" ||
      assigneeFilter !== "all" ||
      dateFilter !== "all" ||
      tagFilter !== "all" ||
      priorityFilter !== "all"
    );
  };

  // Update task assignees
  const updateTaskAssignees = async (taskId: string, assigneeIds: string[]) => {
    try {
      await TasksAPI.updateAssignees(taskId, assigneeIds);
      await loadTasks();
    } catch (err: any) {
      setError("Failed to update task assignees");
    }
  };

  useEffect(() => {
    if (projectId) {
      setLoading(true);
      // Load project first, then load tasks and members
      loadProject()
        .then(() => {
          Promise.all([loadTasks(), loadProjectMembers()]).finally(() => {
            setLoading(false);
          });
        })
        .catch(() => {
          setLoading(false);
        });
    }
  }, [projectId]);

  if (loading) {
    return <ProjectDetailSkeleton />;
  }

  if (error || !project) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || "Project not found"}</p>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
            <p className="text-gray-600">
              Owner: {project.owner_display_name || project.owner_id}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {project.user_role && (
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${
                project.user_role === "owner"
                  ? "bg-yellow-100 text-yellow-800"
                  : project.user_role === "manager"
                  ? "bg-blue-100 text-blue-800"
                  : project.user_role === "admin"
                  ? "bg-purple-100 text-purple-800"
                  : "bg-green-100 text-green-800"
              }`}
            >
              {project.user_role === "owner"
                ? "Owner"
                : project.user_role === "manager"
                ? "Manager"
                : project.user_role === "admin"
                ? "Admin"
                : project.user_role === "staff"
                ? "Staff"
                : project.user_role?.charAt(0).toUpperCase() +
                  project.user_role?.slice(1)}
            </span>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
          {error}
        </div>
      )}

      {/* Collaborators Section */}
      <div className="bg-white rounded-lg border border-gray-200 mb-6">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={() => setShowProjectMembers(!showProjectMembers)}
            className="flex items-center gap-2 w-full text-left hover:bg-gray-50 p-2 -m-2 rounded-md transition-colors"
          >
            {showProjectMembers ? (
              <ChevronDown className="h-5 w-5 text-gray-500" />
            ) : (
              <ChevronRight className="h-5 w-5 text-gray-500" />
            )}
            <UserIcon className="h-5 w-5" />
            <h2 className="text-lg font-semibold text-gray-900">
              Collaborators ({users.length})
            </h2>
          </button>
        </div>
        {showProjectMembers && (
          <div className="p-4">
            {(() => {
              // Check if there are no other collaborators besides the current user
              const otherCollaborators = users.filter(
                (member) => member.id !== user?.id
              );
              const hasNoOtherCollaborators = otherCollaborators.length === 0;

              if (hasNoOtherCollaborators && (project?.user_role === "owner" || project?.user_role === "manager" || user?.id === project?.owner_id)) {
                return (
                  <div className="text-center py-8">
                    <UserIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-gray-500 text-sm">
                      No collaborators added yet.
                    </p>
                  </div>
                );
              }

              if (users.length === 0) {
                return (
                  <div className="text-center py-8">
                    <UserIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-gray-500 text-sm">
                      No collaborators added yet.
                    </p>
                  </div>
                );
              }

              return (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {users.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
                      {(member.display_name || member.email)
                        .charAt(0)
                        .toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {member.display_name || member.email}
                      </p>
                      <p className="text-xs text-gray-500 truncate">
                        {member.email}
                      </p>
                    </div>
                    <Badge
                      variant={
                        member.roles.includes("owner")
                          ? "default"
                          : member.roles.includes("manager")
                          ? "secondary"
                          : "outline"
                      }
                      className={`text-xs ${
                        member.roles.includes("owner") ||
                        member.roles.includes("manager")
                          ? ""
                          : "bg-green-100 text-green-800 border-green-200 hover:bg-green-200"
                      }`}
                    >
                      {member.roles.includes("owner")
                        ? "Owner"
                        : member.roles.includes("manager")
                        ? "Manager"
                        : member.roles.includes("staff")
                        ? "Staff"
                        : "Member"}
                    </Badge>
                  </div>
                ))}
              </div>
              );
            })()}
          </div>
        )}
      </div>

      {/* Overdue Tasks Section */}
      {(() => {
        const overdueTasks = tasks.filter((task) => isTaskOverdue(task));

        if (overdueTasks.length === 0) return null;

        return (
          <div className="bg-red-50 border-2 border-red-200 rounded-lg mb-6 shadow-sm">
            <div className="p-4 border-b border-red-200">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-red-600" />
                <h2 className="text-lg font-semibold text-red-900">
                  Overdue Tasks ({overdueTasks.length})
                </h2>
              </div>
              <p className="text-sm text-red-700 mt-1">
                {overdueTasks.length === 1
                  ? "1 task is past its deadline"
                  : `${overdueTasks.length} tasks are past their deadlines`}
              </p>
            </div>
            <div className="p-4 space-y-3">
              {overdueTasks.map((task) => {
                const getStatusConfig = (status: Task["status"]) => {
                  switch (status) {
                    case "completed":
                      return {
                        color: "bg-green-50 border-green-200",
                        badgeColor:
                          "bg-green-100 text-green-700 border-green-200",
                        accentColor: "bg-green-500",
                      };
                    case "in_progress":
                      return {
                        color: "bg-blue-50 border-blue-200",
                        badgeColor: "bg-blue-100 text-blue-700 border-blue-200",
                        accentColor: "bg-blue-500",
                      };
                    case "blocked":
                      return {
                        color: "bg-red-50 border-red-200",
                        badgeColor: "bg-red-100 text-red-700 border-red-200",
                        accentColor: "bg-red-500",
                      };
                    default:
                      return {
                        color: "bg-white border-gray-200",
                        badgeColor:
                          "bg-gray-100 text-gray-700 border-gray-200",
                        accentColor: "bg-gray-400",
                      };
                  }
                };
                const statusConfig = getStatusConfig(task.status);

                return (
                  <div
                    key={task.id}
                    className={`group relative border-2 rounded-lg transition-all duration-200 hover:shadow-lg cursor-pointer bg-white ${statusConfig.color}`}
                    onClick={() =>
                      router.push(`/projects/${projectId}/tasks/${task.id}`)
                    }
                  >
                    {/* Status Accent Bar */}
                    <div
                      className={`absolute left-0 top-0 bottom-0 w-1 rounded-l-lg ${statusConfig.accentColor}`}
                    />

                    <div className="p-4 pl-5">
                      <div className="flex items-start justify-between gap-4">
                        {/* Main Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start gap-3 mb-2">
                            <h3
                              className={`text-base font-semibold flex-1 ${
                                task.status === "completed"
                                  ? "line-through text-gray-500"
                                  : "text-gray-900 group-hover:text-blue-600 transition-colors"
                              }`}
                            >
                              {task.title}
                            </h3>
                            <Badge
                              className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium border ${statusConfig.badgeColor}`}
                            >
                              {getStatusIcon(task.status)}
                              {task.status === "todo"
                                ? "To Do"
                                : task.status === "in_progress"
                                ? "In Progress"
                                : task.status === "completed"
                                ? "Completed"
                                : task.status === "blocked"
                                ? "Blocked"
                                : (task.status as string)
                                    .charAt(0)
                                    .toUpperCase() +
                                  (task.status as string)
                                    .slice(1)
                                    .replace("_", " ")}
                            </Badge>
                          </div>

                          {task.description && (
                            <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                              {task.description}
                            </p>
                          )}

                          {/* Metadata Row */}
                          <div className="flex items-center gap-4 mt-3 pt-3 border-t border-red-200">
                            {/* Due Date - Highlighted as Overdue */}
                            {task.due_date && (
                              <div className="flex items-center gap-1.5 text-xs text-red-700 font-semibold">
                                <Calendar className="h-4 w-4 text-red-600" />
                                <span>
                                  Overdue:{" "}
                                  {new Date(task.due_date).toLocaleDateString(
                                    "en-US",
                                    {
                                      month: "short",
                                      day: "numeric",
                                      year:
                                        new Date(task.due_date).getFullYear() !==
                                        new Date().getFullYear()
                                          ? "numeric"
                                          : undefined,
                                    }
                                  )}
                                </span>
                              </div>
                            )}

                            {/* Assignees */}
                            {task.assignee_names &&
                              task.assignee_names.length > 0 && (
                                <div className="flex items-center gap-2">
                                  <div className="flex -space-x-2">
                                    {task.assignee_names
                                      .slice(0, 3)
                                      .map((name, index) => (
                                        <div
                                          key={index}
                                          className="w-6 h-6 bg-blue-500 rounded-full border-2 border-white flex items-center justify-center text-white text-xs font-medium"
                                          title={name}
                                        >
                                          {name.charAt(0).toUpperCase()}
                                        </div>
                                      ))}
                                  </div>
                                  {task.assignee_names.length > 3 && (
                                    <span className="text-xs text-gray-500 font-medium">
                                      +{task.assignee_names.length - 3}
                                    </span>
                                  )}
                                </div>
                              )}

                            {/* Priority */}
                            {task.priority && (
                              <div className="flex items-center gap-1.5 text-xs">
                                <Flag className={`h-4 w-4 ${
                                  task.priority >= 8 ? "text-red-500" :
                                  task.priority >= 5 ? "text-orange-500" :
                                  "text-yellow-500"
                                }`} />
                                <span className="font-medium text-gray-600">
                                  Priority {task.priority}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })()}

      {/* Tasks Section */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Tasks</h2>
          <div className="flex items-center gap-2">
            <Button
              variant={
                showFilters || hasActiveFilters() ? "secondary" : "outline"
              }
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2"
            >
              <Filter className="h-4 w-4" />
              Filters
              {hasActiveFilters() && (
                <Badge
                  variant="secondary"
                  className="ml-1 h-5 w-5 p-0 flex items-center justify-center text-xs"
                >
                  {
                    [
                      searchQuery,
                      statusFilter,
                      assigneeFilter,
                      dateFilter,
                      tagFilter,
                    ].filter((f) => f !== "all" && f.trim() !== "").length
                  }
                </Badge>
              )}
            </Button>
            {(project.user_role === "owner" ||
              project.user_role === "manager" ||
              project.user_role === "staff" ||
              canAdminManage(user)) && (
              <Button
                onClick={() => setShowCreateTaskModal(true)}
                size="sm"
                className="flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Add Task
              </Button>
            )}
          </div>
        </div>

        {/* Filter Controls */}
        {showFilters && (
          <div className="p-6 border-b border-gray-200 bg-gray-50/50">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
              {/* Search */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">
                  Search
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search tasks..."
                    className="pl-10"
                  />
                </div>
              </div>

              {/* Status Filter */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">
                  Status
                </label>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="todo">To Do</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="blocked">Blocked</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Assignee Filter */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">
                  Assignee
                </label>
                <Select
                  value={assigneeFilter}
                  onValueChange={setAssigneeFilter}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="All Assignees" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Assignees</SelectItem>
                    <SelectItem value="unassigned">Unassigned</SelectItem>
                    {users.map((user) => (
                      <SelectItem key={user.id} value={user.id}>
                        {user.display_name || user.email}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Date Filter */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">
                  Due Date
                </label>
                <Select value={dateFilter} onValueChange={setDateFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Dates" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Dates</SelectItem>
                    <SelectItem value="overdue">Overdue</SelectItem>
                    <SelectItem value="today">Today</SelectItem>
                    <SelectItem value="this_week">This Week</SelectItem>
                    <SelectItem value="this_month">This Month</SelectItem>
                    <SelectItem value="no_date">No Date</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Tag Filter */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">
                  Tags
                </label>
                <Select value={tagFilter} onValueChange={setTagFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Tags" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Tags</SelectItem>
                    <SelectItem value="no_tags">No Tags</SelectItem>
                    {getAllTags().map((tag) => (
                      <SelectItem key={tag} value={tag}>
                        {tag.charAt(0).toUpperCase() + tag.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Priority Filter */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">
                  Priority
                </label>
                <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Priorities" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Priorities</SelectItem>
                    <SelectItem value="no_priority">No Priority</SelectItem>
                    <SelectItem value="highest_to_lowest">Highest to Lowest</SelectItem>
                    <SelectItem value="lowest_to_highest">Lowest to Highest</SelectItem>
                    {Array.from({ length: 10 }, (_, i) => i + 1).map((priority) => (
                      <SelectItem key={priority} value={priority.toString()}>
                        Priority {priority}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Clear Filters */}
            {hasActiveFilters() && (
              <div className="mt-6 flex justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFilters}
                  className="flex items-center gap-2 text-gray-600 hover:text-gray-800"
                >
                  <X className="h-4 w-4" />
                  Clear all filters
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Tasks List */}
        <div className="p-4">
          {loadingTasks ? (
            <TaskListSkeleton />
          ) : tasks.length === 0 ? (
            <div className="text-center py-8">
              <Clock className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-500 text-sm mb-1">No tasks yet</p>
              <p className="text-gray-400 text-xs">
                Create your first task to get started
              </p>
            </div>
          ) : getFilteredTasks().length === 0 ? (
            <div className="text-center py-8">
              <Search className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-500 text-sm mb-1">
                No tasks match your filters
              </p>
              <p className="text-gray-400 text-xs">
                Try adjusting your search criteria or clear filters
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {getFilteredTasks().map((task) => {
                const getStatusConfig = (status: Task["status"]) => {
                  switch (status) {
                    case "completed":
                      return {
                        color: "bg-green-50 border-green-200",
                        badgeColor: "bg-green-100 text-green-700 border-green-200",
                        accentColor: "bg-green-500",
                      };
                    case "in_progress":
                      return {
                        color: "bg-blue-50 border-blue-200",
                        badgeColor: "bg-blue-100 text-blue-700 border-blue-200",
                        accentColor: "bg-blue-500",
                      };
                    case "blocked":
                      return {
                        color: "bg-red-50 border-red-200",
                        badgeColor: "bg-red-100 text-red-700 border-red-200",
                        accentColor: "bg-red-500",
                      };
                    default:
                      return {
                        color: "bg-white border-gray-200",
                        badgeColor: "bg-gray-100 text-gray-700 border-gray-200",
                        accentColor: "bg-gray-400",
                      };
                  }
                };
                const statusConfig = getStatusConfig(task.status);

                return (
                  <div
                    key={task.id}
                    className={`group relative border-2 rounded-lg transition-all duration-200 hover:shadow-lg cursor-pointer ${statusConfig.color}`}
                    onClick={() =>
                      router.push(`/projects/${projectId}/tasks/${task.id}`)
                    }
                  >
                    {/* Status Accent Bar */}
                    <div
                      className={`absolute left-0 top-0 bottom-0 w-1 rounded-l-lg ${statusConfig.accentColor}`}
                    />

                    <div className="p-5 pl-6">
                      <div className="flex items-start justify-between gap-4">
                        {/* Main Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start gap-3 mb-2">
                            <h3
                              className={`text-base font-semibold flex-1 ${
                                task.status === "completed"
                                  ? "line-through text-gray-500"
                                  : "text-gray-900 group-hover:text-blue-600 transition-colors"
                              }`}
                            >
                              {task.title}
                            </h3>
                            <Badge
                              className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium border ${statusConfig.badgeColor}`}
                            >
                              {getStatusIcon(task.status)}
                              {task.status === "todo"
                                ? "To Do"
                                : task.status === "in_progress"
                                ? "In Progress"
                                : task.status === "completed"
                                ? "Completed"
                                : task.status === "blocked"
                                ? "Blocked"
                                : (task.status as string)
                                    .charAt(0)
                                    .toUpperCase() +
                                  (task.status as string)
                                    .slice(1)
                                    .replace("_", " ")}
                            </Badge>
                          </div>

                          {task.description && (
                            <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                              {task.description}
                            </p>
                          )}

                          {/* Tags */}
                          {task.tags && task.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-3">
                              {task.tags.slice(0, 3).map((tag, index) => (
                                <Badge
                                  key={index}
                                  variant="secondary"
                                  className="text-xs px-2 py-0.5 bg-gray-100 text-gray-700 hover:bg-gray-200"
                                >
                                  <Tag className="h-3 w-3 mr-1" />
                                  {tag.charAt(0).toUpperCase() + tag.slice(1)}
                                </Badge>
                              ))}
                              {task.tags.length > 3 && (
                                <Badge
                                  variant="outline"
                                  className="text-xs px-2 py-0.5 text-gray-500 border-gray-300"
                                >
                                  +{task.tags.length - 3} more
                                </Badge>
                              )}
                            </div>
                          )}

                          {/* Metadata Row */}
                          <div className="flex items-center gap-4 mt-4 pt-3 border-t border-gray-200">
                            {/* Assignees Display */}
                            <div className="flex items-center gap-2">
                              {editingAssignees === task.id ? (
                                <div
                                  className="min-w-[200px]"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <AssigneeSelector
                                    users={users}
                                    selectedUserIds={tempAssigneeIds}
                                    onSelectionChange={setTempAssigneeIds}
                                    maxAssignees={5}
                                    placeholder="Select project members"
                                  />
                                  <div className="flex gap-2 mt-2">
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        updateTaskAssignees(
                                          task.id,
                                          tempAssigneeIds
                                        );
                                        setEditingAssignees(null);
                                      }}
                                      className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700 transition-colors"
                                    >
                                      Save
                                    </button>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setEditingAssignees(null);
                                        setTempAssigneeIds([]);
                                      }}
                                      className="px-3 py-1.5 bg-gray-300 text-gray-700 text-xs rounded-md hover:bg-gray-400 transition-colors"
                                    >
                                      Cancel
                                    </button>
                                  </div>
                                  {users.length === 0 && (
                                    <div className="text-xs text-orange-600 bg-orange-50 p-2 rounded-md mt-2">
                                      No project members available for assignment
                                    </div>
                                  )}
                                </div>
                              ) : (
                                <div className="flex items-center gap-2">
                                  {task.assignee_names &&
                                  task.assignee_names.length > 0 ? (
                                    <div className="flex items-center gap-2">
                                      <div className="flex -space-x-2">
                                        {task.assignee_names
                                          .slice(0, 3)
                                          .map((name, index) => (
                                            <div
                                              key={index}
                                              className="w-6 h-6 bg-blue-500 rounded-full border-2 border-white flex items-center justify-center text-white text-xs font-medium"
                                              title={name}
                                            >
                                              {name.charAt(0).toUpperCase()}
                                            </div>
                                          ))}
                                      </div>
                                      {task.assignee_names.length > 3 && (
                                        <span className="text-xs text-gray-500 font-medium">
                                          +{task.assignee_names.length - 3}
                                        </span>
                                      )}
                                      <span className="text-xs text-gray-500">
                                        {task.assignee_names.length}{" "}
                                        {task.assignee_names.length === 1
                                          ? "assignee"
                                          : "assignees"}
                                      </span>
                                    </div>
                                  ) : (
                                    <div className="flex items-center gap-1.5 text-xs text-gray-400">
                                      <UserIcon className="h-4 w-4" />
                                      <span>Unassigned</span>
                                    </div>
                                  )}
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setEditingAssignees(task.id);
                                      setTempAssigneeIds(
                                        task.assignee_ids || []
                                      );
                                    }}
                                    className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors opacity-0 group-hover:opacity-100"
                                    title="Edit assignees"
                                  >
                                    <Edit className="h-3.5 w-3.5" />
                                  </button>
                                </div>
                              )}
                            </div>

                            {/* Due Date */}
                            {task.due_date && (
                              <div className="flex items-center gap-1.5 text-xs text-gray-600">
                                <Calendar className="h-4 w-4 text-gray-400" />
                                <span className="font-medium">
                                  {new Date(task.due_date).toLocaleDateString(
                                    "en-US",
                                    {
                                      month: "short",
                                      day: "numeric",
                                      year:
                                        new Date(task.due_date).getFullYear() !==
                                        new Date().getFullYear()
                                          ? "numeric"
                                          : undefined,
                                    }
                                  )}
                                </span>
                              </div>
                            )}

                            {/* Priority */}
                            {task.priority && (
                              <div className="flex items-center gap-1.5 text-xs">
                                <Flag className={`h-4 w-4 ${
                                  task.priority >= 8 ? "text-red-500" :
                                  task.priority >= 5 ? "text-orange-500" :
                                  "text-yellow-500"
                                }`} />
                                <span className="font-medium text-gray-600">
                                  Priority {task.priority}
                                </span>
                              </div>
                            )}

                            {/* Archive Button */}
                            {!(isAdmin(user) && !canAdminManage(user)) && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setConfirmDialog({
                                    isOpen: true,
                                    title: "Archive Task",
                                    description: `Are you sure you want to archive "${task.title}"?`,
                                    variant: "default",
                                    onConfirm: () => archiveTask(task.id),
                                  });
                                }}
                                className="ml-auto p-1.5 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-md transition-colors opacity-0 group-hover:opacity-100"
                                title="Archive task"
                              >
                                <Archive className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Create Task Modal */}
      <CreateTaskModal
        isOpen={showCreateTaskModal}
        onClose={() => setShowCreateTaskModal(false)}
        onSubmit={createTask}
        users={users}
        isLoading={creatingTask}
      />

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={confirmDialog.isOpen}
        onClose={() => setConfirmDialog({ ...confirmDialog, isOpen: false })}
        onConfirm={confirmDialog.onConfirm}
        title={confirmDialog.title}
        description={confirmDialog.description}
        variant={confirmDialog.variant}
        confirmText="Confirm"
      />
    </div>
  );
}
