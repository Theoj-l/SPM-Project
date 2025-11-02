"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { ProjectsAPI, TasksAPI, Project, Task } from "@/lib/api";
import { isAdmin, isManager } from "@/utils/role-utils";
import {
  Archive,
  ArrowLeft,
  RotateCcw,
  CheckSquare,
  Clock,
  AlertCircle,
  Calendar,
  User as UserIcon,
  Folder,
  Users,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";

export default function ArchivedPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [archivedProjects, setArchivedProjects] = useState<Project[]>([]);
  const [archivedTasks, setArchivedTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [restoringTask, setRestoringTask] = useState<string | null>(null);
  const [restoringProject, setRestoringProject] = useState<string | null>(null);

  // Load archived projects and tasks
  const loadArchivedData = async () => {
    try {
      setLoading(true);
      const projectsData = await ProjectsAPI.list(true); // Include archived projects
      setProjects(projectsData);

      // Get archived projects (only for managers/admins)
      const archivedProjectsData = projectsData.filter(
        (project) => project.status === "archived"
      );
      setArchivedProjects(archivedProjectsData);

      // Get archived tasks from all projects
      const allArchivedTasks: Task[] = [];
      for (const project of projectsData) {
        try {
          // Get all tasks for this project (including archived)
          const tasks = await TasksAPI.list(project.id, true);
          const projectArchivedTasks = tasks.filter(
            (task) => task.type === "archived"
          );
          allArchivedTasks.push(...projectArchivedTasks);
        } catch (err) {
          console.error(
            `Failed to load tasks for project ${project.name}:`,
            err
          );
        }
      }

      setArchivedTasks(allArchivedTasks);
    } catch (err: any) {
      setError("Failed to load archived data");
    } finally {
      setLoading(false);
    }
  };

  // Restore a task
  const restoreTask = async (taskId: string) => {
    try {
      setRestoringTask(taskId);
      await TasksAPI.restore(taskId);
      await loadArchivedData(); // Reload to update the list
    } catch (err: any) {
      setError("Failed to restore task");
    } finally {
      setRestoringTask(null);
    }
  };

  // Restore a project
  const restoreProject = async (projectId: string) => {
    try {
      setRestoringProject(projectId);
      await ProjectsAPI.restore(projectId);
      await loadArchivedData(); // Reload to update the list
    } catch (err: any) {
      setError("Failed to restore project");
    } finally {
      setRestoringProject(null);
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
        return <CheckSquare className="h-3 w-3" />;
      case "in_progress":
        return <Clock className="h-3 w-3" />;
      case "completed":
        return <CheckSquare className="h-3 w-3" />;
      case "blocked":
        return <AlertCircle className="h-3 w-3" />;
      default:
        return <CheckSquare className="h-3 w-3" />;
    }
  };

  // Get project name by ID
  const getProjectName = (projectId: string) => {
    const project = projects.find((p) => p.id === projectId);
    return project?.name || "Unknown Project";
  };

  // Check if user can see project archive (managers only)
  const canSeeProjectArchive = () => {
    return isAdmin(user) || isManager(user);
  };

  // Check if user can see task archive (project managers and assignees)
  const canSeeTaskArchive = () => {
    if (isAdmin(user) || isManager(user)) return true;

    // Check if user is assigned to any archived tasks
    return archivedTasks.some((task) =>
      task.assignee_ids?.includes(user?.id || "")
    );
  };

  useEffect(() => {
    loadArchivedData();
  }, []);

  if (loading) {
    return <ArchivedTasksSkeleton />;
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Archive</h1>
            <p className="text-gray-600">Manage archived projects and tasks</p>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      <div className="space-y-8">
        {/* Project Archive Section - Managers Only */}
        {canSeeProjectArchive() && (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Folder className="h-5 w-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900">
                Project Archive
              </h2>
              <span className="text-sm text-gray-500">
                ({archivedProjects.length} archived)
              </span>
            </div>

            {archivedProjects.length === 0 ? (
              <div className="text-center py-8 bg-gray-50 rounded-lg">
                <Folder className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-500">No archived projects</p>
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200">
                <div className="divide-y divide-gray-200">
                  {archivedProjects.map((project) => (
                    <div
                      key={project.id}
                      className="p-4 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-sm font-medium text-gray-900 truncate">
                              {project.name}
                            </h3>
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                              <Archive className="h-3 w-3 mr-1" />
                              Archived
                            </span>
                          </div>

                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            <span className="flex items-center gap-1">
                              <Users className="h-3 w-3" />
                              Owner: {project.owner_display_name || "Unknown"}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 ml-4">
                          <Link
                            href={`/projects/${project.id}`}
                            className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                          >
                            View
                          </Link>
                          <button
                            onClick={() => {
                              if (
                                confirm(
                                  "Are you sure you want to restore this project?"
                                )
                              ) {
                                restoreProject(project.id);
                              }
                            }}
                            disabled={restoringProject === project.id}
                            className="flex items-center gap-1 px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            <RotateCcw className="h-3 w-3" />
                            {restoringProject === project.id
                              ? "Restoring..."
                              : "Restore"}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Task Archive Section - Project Managers and Assignees */}
        {canSeeTaskArchive() && (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <CheckSquare className="h-5 w-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900">
                Task Archive
              </h2>
              <span className="text-sm text-gray-500">
                ({archivedTasks.length} archived)
              </span>
            </div>

            {archivedTasks.length === 0 ? (
              <div className="text-center py-8 bg-gray-50 rounded-lg">
                <CheckSquare className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-500">No archived tasks</p>
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200">
                <div className="divide-y divide-gray-200">
                  {archivedTasks.map((task) => (
                    <div
                      key={task.id}
                      className="p-4 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-sm font-medium text-gray-900 truncate">
                              {task.title}
                            </h3>
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                                task.status
                              )}`}
                            >
                              {getStatusIcon(task.status)}
                              {task.status.replace("_", " ")}
                            </span>
                          </div>

                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            <span className="flex items-center gap-1">
                              <Folder className="h-3 w-3" />
                              {getProjectName(task.project_id || "")}
                            </span>

                            {task.assignee_names &&
                              task.assignee_names.length > 0 && (
                                <span className="flex items-center gap-1">
                                  <UserIcon className="h-3 w-3" />
                                  {task.assignee_names.join(", ")}
                                </span>
                              )}

                            {task.due_date && (
                              <span className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                {new Date(task.due_date).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 ml-4">
                          <Link
                            href={`/projects/${task.project_id}/tasks/${task.id}`}
                            className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                          >
                            View
                          </Link>
                          <button
                            onClick={() => {
                              if (
                                confirm(
                                  "Are you sure you want to restore this task?"
                                )
                              ) {
                                restoreTask(task.id);
                              }
                            }}
                            disabled={restoringTask === task.id}
                            className="flex items-center gap-1 px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            <RotateCcw className="h-3 w-3" />
                            {restoringTask === task.id
                              ? "Restoring..."
                              : "Restore"}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* No Access Message */}
        {!canSeeProjectArchive() && !canSeeTaskArchive() && (
          <div className="text-center py-12">
            <Archive className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No Archive Access
            </h3>
            <p className="text-gray-500">
              You don't have permission to view archived projects or tasks.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// Skeleton component for loading state
function ArchivedTasksSkeleton() {
  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex items-center gap-4 mb-6">
        <Skeleton className="h-9 w-9" />
        <div>
          <Skeleton className="h-8 w-32 mb-2" />
          <Skeleton className="h-4 w-48" />
        </div>
      </div>

      <div className="space-y-8">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Skeleton className="h-5 w-5" />
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-16" />
          </div>
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="p-4">
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-3 w-3/4" />
            </div>
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2 mb-4">
            <Skeleton className="h-5 w-5" />
            <Skeleton className="h-6 w-28" />
            <Skeleton className="h-4 w-16" />
          </div>
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="p-4">
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-3 w-3/4" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
