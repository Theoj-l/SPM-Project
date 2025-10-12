"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { ProjectsAPI, Project } from "@/lib/api";
import ProjectMemberManager from "@/components/ProjectMemberManager";
import { isAdmin, isManager } from "@/utils/role-utils";
import { Plus, Users, Folder, Trash2, Crown, Shield, User } from "lucide-react";

export default function Home() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [projectName, setProjectName] = useState("");
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load user's projects
  const loadProjects = async () => {
    try {
      const data = await ProjectsAPI.list();
      setProjects(data);
    } catch (err: any) {
      setError("Failed to load projects");
    }
  };

  // Create new project
  const createProject = async () => {
    if (!projectName.trim()) {
      setError("Project name is required");
      return;
    }

    setLoading(true);
    try {
      await ProjectsAPI.create(projectName.trim());
      setProjectName("");
      setShowCreateProject(false);
      await loadProjects();
    } catch (err: any) {
      setError(err.message || "Failed to create project");
    } finally {
      setLoading(false);
    }
  };

  // Delete project
  const deleteProject = async (projectId: string, projectName: string) => {
    if (
      !confirm(
        `Are you sure you want to delete the project "${projectName}"? This action cannot be undone.`
      )
    ) {
      return;
    }

    try {
      await ProjectsAPI.delete(projectId);
      await loadProjects();
    } catch (err: any) {
      setError(err.message || "Failed to delete project");
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
        return <User className="h-4 w-4 text-green-500" />;
      default:
        return <User className="h-4 w-4 text-gray-500" />;
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
    if (user) {
      loadProjects();
    }
  }, [user]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Workspace</h1>
        <p className="text-muted-foreground">Welcome to your Jite workspace</p>
      </div>

      {/* Project Management - Show for all users */}
      {user && (
        <div className="space-y-6">
          {/* Project Management Section */}
          <div className="rounded-lg border bg-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Folder className="h-5 w-5" />
                My Projects
              </h2>
              {(isManager(user) || isAdmin(user)) && (
                <button
                  onClick={() => setShowCreateProject(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Plus className="h-4 w-4" />
                  Create Project
                </button>
              )}
            </div>

            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                {error}
              </div>
            )}

            {/* Create Project Form - Only for managers/admins */}
            {showCreateProject && (isManager(user) || isAdmin(user)) && (
              <div className="mb-6 p-4 border rounded-lg bg-gray-50">
                <h3 className="text-lg font-medium mb-3">Create New Project</h3>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    placeholder="Enter project name"
                    className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    autoFocus
                  />
                  <button
                    onClick={createProject}
                    disabled={loading}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                  >
                    {loading ? "Creating..." : "Create"}
                  </button>
                  <button
                    onClick={() => {
                      setShowCreateProject(false);
                      setProjectName("");
                      setError("");
                    }}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Projects List */}
            <div>
              <h3 className="text-lg font-medium mb-3">
                Projects You're In ({projects.length})
              </h3>
              {projects.length === 0 ? (
                <div className="text-center py-12">
                  <Folder className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 text-lg mb-2">No projects yet</p>
                  <p className="text-gray-400 text-sm">
                    {isManager(user) || isAdmin(user)
                      ? "Create your first project or ask to be added to one!"
                      : "Ask your manager to add you to a project!"}
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {projects.map((project) => (
                    <div
                      key={project.id}
                      className="bg-white border rounded-lg p-6 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <Folder className="h-6 w-6 text-blue-500" />
                          <div>
                            <h3 className="font-semibold text-lg">
                              {project.name}
                            </h3>
                            {project.user_role && (
                              <span
                                className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 w-fit mt-1 ${getRoleColor(
                                  project.user_role
                                )}`}
                              >
                                {getRoleIcon(project.user_role)}
                                {project.user_role}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="mb-4">
                        <p className="text-sm text-gray-600">
                          <span className="font-medium">Owner:</span>{" "}
                          {project.owner_display_name || project.owner_id}
                        </p>
                      </div>

                      <div className="flex gap-2">
                        {(project.user_role === "owner" ||
                          project.user_role === "manager") && (
                          <button
                            onClick={() => setSelectedProject(project)}
                            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
                          >
                            <Users className="h-4 w-4" />
                            Manage
                          </button>
                        )}
                        {project.user_role === "owner" && (
                          <button
                            onClick={() =>
                              deleteProject(project.id, project.name)
                            }
                            className="flex items-center justify-center gap-2 px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Project Member Manager Modal */}
      {selectedProject && (
        <ProjectMemberManager
          projectId={selectedProject.id}
          projectName={selectedProject.name}
          onClose={() => setSelectedProject(null)}
        />
      )}
    </div>
  );
}
