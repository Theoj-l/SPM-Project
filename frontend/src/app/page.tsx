"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { ProjectsAPI, Project } from "@/lib/api";
import ProjectMemberManager from "@/components/ProjectMemberManager";
import DeleteConfirmationDialog from "@/components/DeleteConfirmationDialog";
import ProjectCard from "@/components/ProjectCard";
import ProjectCardSkeleton from "@/components/ProjectCardSkeleton";
import { isAdmin, hasManagerRole, canAdminManage } from "@/utils/role-utils";
import { Plus, Folder, Search, Filter } from "lucide-react";

export default function Home() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [allProjects, setAllProjects] = useState<Project[]>([]);
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [projectName, setProjectName] = useState("");
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [error, setError] = useState("");
  const [deleteDialog, setDeleteDialog] = useState<{
    isOpen: boolean;
    project: Project | null;
  }>({ isOpen: false, project: null });

  // Admin filtering states
  const [showAllProjects, setShowAllProjects] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<
    "all" | "active" | "archived"
  >("all");
  const [ownerFilter, setOwnerFilter] = useState("");

  // Load user's projects
  const loadProjects = async () => {
    try {
      setLoadingProjects(true);
      const data = await ProjectsAPI.list();
      setProjects(data);
    } catch {
      setError("Failed to load projects");
    } finally {
      setLoadingProjects(false);
    }
  };

  // Load all projects (admin only)
  const loadAllProjects = async () => {
    try {
      setLoadingProjects(true);
      const data = await ProjectsAPI.listAll(true); // Include archived
      setAllProjects(data);
    } catch {
      setError("Failed to load all projects");
    } finally {
      setLoadingProjects(false);
    }
  };

  // Filter projects based on search and filters
  const getFilteredProjects = () => {
    let filtered = showAllProjects ? allProjects : projects;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(
        (project) =>
          project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          project.owner_display_name
            ?.toLowerCase()
            .includes(searchTerm.toLowerCase())
      );
    }

    // Apply status filter
    if (statusFilter !== "all") {
      filtered = filtered.filter(
        (project) =>
          project.status === statusFilter ||
          (!project.status && statusFilter === "active")
      );
    }

    // Apply owner filter
    if (ownerFilter) {
      filtered = filtered.filter((project) =>
        project.owner_display_name
          ?.toLowerCase()
          .includes(ownerFilter.toLowerCase())
      );
    }

    return filtered;
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
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setLoading(false);
    }
  };

  // Show delete confirmation dialog
  const showDeleteDialog = (project: Project) => {
    setDeleteDialog({ isOpen: true, project });
  };

  // Confirm delete project
  const confirmDeleteProject = async () => {
    if (!deleteDialog.project) return;

    try {
      setLoading(true);
      await ProjectsAPI.archive(deleteDialog.project.id);
      await loadProjects();
      setDeleteDialog({ isOpen: false, project: null });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to archive project");
    } finally {
      setLoading(false);
    }
  };

  // Close delete dialog
  const closeDeleteDialog = () => {
    setDeleteDialog({ isOpen: false, project: null });
  };

  useEffect(() => {
    if (user) {
      loadProjects();
      if (isAdmin(user)) {
        loadAllProjects();
      }
    }
  }, [user]);

  // Toggle between user projects and all projects (admin only)
  const toggleProjectView = () => {
    setShowAllProjects(!showAllProjects);
    setSearchTerm("");
    setStatusFilter("all");
    setOwnerFilter("");
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Workspace</h1>
        <p className="text-muted-foreground">Welcome to your Jite workspace</p>
      </div>

      {/* Projects Section - For all users */}
      {user && (
        <div className="space-y-4">
          <div className="rounded-lg border bg-white">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b">
              <div className="flex items-center gap-2">
                <Folder className="h-4 w-4 text-blue-500" />
                <h2 className="text-lg font-semibold">
                  {showAllProjects ? "All Projects" : "My Projects"}
                </h2>
                <span className="text-sm text-gray-500">
                  ({getFilteredProjects().length})
                </span>
              </div>
              <div className="flex items-center gap-2">
                {isAdmin(user) && (
                  <button
                    onClick={toggleProjectView}
                    className={`px-3 py-1.5 rounded-md text-sm font-medium ${
                      showAllProjects
                        ? "bg-gray-600 text-white hover:bg-gray-700"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                  >
                    {showAllProjects ? "My Projects" : "All Projects"}
                  </button>
                )}
                {(hasManagerRole(user) || canAdminManage(user)) && (
                  <button
                    onClick={() => setShowCreateProject(true)}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
                  >
                    <Plus className="h-4 w-4" />
                    New
                  </button>
                )}
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mx-4 mt-3 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
                {error}
              </div>
            )}

            {/* Quick Search (all users) */}
            {!((isAdmin(user)) && showAllProjects) && (
              <div className="p-4 border-b bg-gray-50">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search projects..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-3 py-2 border rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
                  />
                </div>
              </div>
            )}

            {/* Admin Filtering Controls */}
            {isAdmin(user) && showAllProjects && (
              <div className="p-4 border-b bg-gray-50">
                <div className="flex flex-col gap-3">
                  {/* Search */}
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search projects or owners..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-3 py-2 border rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    />
                  </div>

                  {/* Filters Row */}
                  <div className="flex gap-3">
                    {/* Status Filter */}
                    <div className="flex items-center gap-2">
                      <Filter className="h-4 w-4 text-gray-500" />
                      <select
                        value={statusFilter}
                        onChange={(e) =>
                          setStatusFilter(
                            e.target.value as "all" | "active" | "archived"
                          )
                        }
                        className="px-3 py-1.5 border rounded-md text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="all">All Status</option>
                        <option value="active">Active</option>
                        <option value="archived">Archived</option>
                      </select>
                    </div>

                    {/* Owner Filter */}
                    <div className="flex-1">
                      <input
                        type="text"
                        placeholder="Filter by owner..."
                        value={ownerFilter}
                        onChange={(e) => setOwnerFilter(e.target.value)}
                        className="w-full px-3 py-1.5 border rounded-md text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Create Project Form */}
            {showCreateProject &&
              (hasManagerRole(user) || canAdminManage(user)) && (
                <div className="p-4 border-b bg-gray-50">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={projectName}
                      onChange={(e) => setProjectName(e.target.value)}
                      placeholder="Project name"
                      className="flex-1 px-3 py-2 border rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
                      autoFocus
                    />
                    <button
                      onClick={createProject}
                      disabled={loading}
                      className="px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 text-sm"
                    >
                      {loading ? "Creating..." : "Create"}
                    </button>
                    <button
                      onClick={() => {
                        setShowCreateProject(false);
                        setProjectName("");
                        setError("");
                      }}
                      className="px-3 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

            {/* Projects Grid */}
            <div className="p-4">
              {loadingProjects ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Array.from({ length: 6 }).map((_, index) => (
                    <ProjectCardSkeleton key={index} />
                  ))}
                </div>
              ) : getFilteredProjects().length === 0 ? (
                <div className="text-center py-8">
                  <Folder className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-500 text-sm mb-1">
                    {showAllProjects ? "No projects found" : "No projects yet"}
                  </p>
                  <p className="text-gray-400 text-xs">
                    {showAllProjects
                      ? "Try adjusting your filters"
                      : hasManagerRole(user) || canAdminManage(user)
                      ? "Create your first project"
                      : "Ask your manager to add you to a project"}
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {getFilteredProjects().map((project) => (
                    <ProjectCard
                      key={project.id}
                      project={project}
                      onManageMembers={setSelectedProject}
                      onArchive={showDeleteDialog}
                    />
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

      {/* Delete Confirmation Dialog */}
      <DeleteConfirmationDialog
        isOpen={deleteDialog.isOpen}
        onClose={closeDeleteDialog}
        onConfirm={confirmDeleteProject}
        title="Archive Project"
        description="This will hide the project from the main view."
        itemName={deleteDialog.project?.name || ""}
        isLoading={loading}
      />
    </div>
  );
}
