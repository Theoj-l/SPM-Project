"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { ProjectsAPI, Project } from "@/lib/api";
import { Plus, Folder, X } from "lucide-react";
import { hasManagerRole, canAdminManage } from "@/utils/role-utils";

export default function ProjectsPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [showInput, setShowInput] = useState(false);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Load all projects for current user
  const loadProjects = async () => {
    setLoading(true);
    try {
      const data = await ProjectsAPI.list();
      setProjects(data);
    } catch (e: any) {
      setError("Failed to fetch");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  // Create project (with validation)
  const createProject = async () => {
    if (!name.trim()) {
      setError("Project name is required.");
      return;
    }
    try {
      await ProjectsAPI.create(name);
      setName("");
      setShowInput(false);
      await loadProjects();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div className="mx-auto max-w-6xl p-6">
      {/* Header Section */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Projects</h1>
        {(hasManagerRole(user) || canAdminManage(user)) && !showInput && (
          <button
            onClick={() => setShowInput(true)}
            className="inline-flex items-center gap-2 rounded-xl px-4 py-2 bg-black text-white hover:bg-gray-800"
          >
            <Plus className="h-4 w-4" /> Create Project
          </button>
        )}
        {showInput && (
          <div className="flex gap-2 items-center">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter project name"
              className="border rounded-lg px-3 py-2"
              autoFocus
            />
            <button
              onClick={createProject}
              className="rounded-xl px-4 py-2 bg-black text-white hover:bg-gray-800"
            >
              Save
            </button>
            <button
              onClick={() => {
                setShowInput(false);
                setName("");
                setError("");
              }}
              className="p-2 rounded-xl bg-gray-200 hover:bg-gray-300"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && <p className="text-red-600 mb-3">{error}</p>}

      {/* Project Grid */}
      {loading ? (
        <p className="text-gray-500">Loading projects...</p>
      ) : projects.length === 0 ? (
        <p className="text-gray-500">No projects found.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((p) => (
            <div
              key={p.id}
              className="rounded-2xl shadow hover:shadow-lg transition overflow-hidden bg-white cursor-default"
            >
              <div className="h-36 bg-gray-100 relative">
                {p.cover_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={p.cover_url}
                    alt=""
                    className="absolute inset-0 w-full h-full object-cover"
                  />
                ) : (
                  <div className="h-full w-full flex items-center justify-center text-gray-400">
                    <Folder className="w-10 h-10" />
                  </div>
                )}
              </div>
              <div className="p-4">
                <div className="font-medium">{p.name}</div>
                <div className="text-sm text-gray-500">
                  Owner: {p.owner_id.slice(0, 6)}...
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
