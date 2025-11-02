"use client";

import { Project } from "@/lib/api";
import { useRouter } from "next/navigation";
import { Folder, Users, Archive, Crown, Shield, User } from "lucide-react";
import { canAdminManage, isAdmin } from "@/utils/role-utils";
import { useAuth } from "@/contexts/AuthContext";

interface ProjectCardProps {
  project: Project;
  onManageMembers: (project: Project) => void;
  onArchive: (project: Project) => void;
}

export default function ProjectCard({
  project,
  onManageMembers,
  onArchive,
}: ProjectCardProps) {
  const router = useRouter();
  const { user } = useAuth();

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

  const handleCardClick = () => {
    router.push(`/projects/${project.id}`);
  };

  const handleManageMembers = (e: React.MouseEvent) => {
    e.stopPropagation();
    onManageMembers(project);
  };

  const handleArchive = (e: React.MouseEvent) => {
    e.stopPropagation();
    onArchive(project);
  };

  return (
    <div
      onClick={handleCardClick}
      className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md hover:border-blue-300 transition-all duration-200 cursor-pointer group"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Folder className="h-5 w-5 text-blue-500 flex-shrink-0" />
          <h3 className="font-semibold text-gray-900 truncate group-hover:text-blue-600 transition-colors">
            {project.name}
          </h3>
        </div>

        {/* Role Badge */}
        {project.user_role && (
          <span
            className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 flex-shrink-0 ${getRoleColor(
              project.user_role
            )}`}
          >
            {getRoleIcon(project.user_role)}
            {project.user_role}
          </span>
        )}
      </div>

      {/* Project Info */}
      <div className="space-y-2 mb-4">
        <p className="text-sm text-gray-600">
          <span className="font-medium">Owner:</span>{" "}
          {project.owner_display_name || project.owner_id}
        </p>
        {project.status && (
          <p className="text-sm text-gray-600">
            <span className="font-medium">Status:</span>
            <span
              className={`ml-1 px-2 py-0.5 rounded text-xs ${
                project.status === "active"
                  ? "bg-green-100 text-green-800"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              {project.status}
            </span>
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div className="flex items-center gap-1">
          {(project.user_role === "owner" ||
            project.user_role === "manager") && (
            <button
              onClick={handleManageMembers}
              className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
              title="Manage Members"
            >
              <Users className="h-4 w-4" />
            </button>
          )}
        </div>

        {project.user_role === "owner" &&
          !(isAdmin(user) && !canAdminManage(user)) && (
            <button
              onClick={handleArchive}
              className="p-1.5 text-gray-500 hover:text-orange-600 hover:bg-orange-50 rounded transition-colors"
              title="Archive Project"
            >
              <Archive className="h-4 w-4" />
            </button>
          )}
      </div>
    </div>
  );
}
