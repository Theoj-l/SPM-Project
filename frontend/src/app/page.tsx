"use client";

import { useAuth } from "@/contexts/AuthContext";
import {
  getUserRoleNames,
  isAdmin,
  isManager,
  isStaff,
} from "@/utils/role-utils";

export default function Home() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Workspace</h1>
        <p className="text-muted-foreground">Welcome to your Jite workspace</p>
      </div>

      {/* User Role Information */}
      {user && (
        <div className="rounded-lg border bg-card p-6">
          <h2 className="text-xl font-semibold mb-4">User Information</h2>
          <div className="space-y-2">
            <p>
              <strong>Email:</strong> {user.email}
            </p>
            <p>
              <strong>Roles:</strong> {getUserRoleNames(user).join(", ")}
            </p>
            <p>
              <strong>Role IDs:</strong> [{user.roles?.join(", ") || "none"}]
            </p>
            <div className="flex gap-4 mt-4">
              <span
                className={`px-2 py-1 rounded text-sm ${
                  isStaff(user)
                    ? "bg-green-100 text-green-800"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                Staff Access: {isStaff(user) ? "Yes" : "No"}
              </span>
              <span
                className={`px-2 py-1 rounded text-sm ${
                  isManager(user)
                    ? "bg-blue-100 text-blue-800"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                Manager Access: {isManager(user) ? "Yes" : "No"}
              </span>
              <span
                className={`px-2 py-1 rounded text-sm ${
                  isAdmin(user)
                    ? "bg-red-100 text-red-800"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                Admin Access: {isAdmin(user) ? "Yes" : "No"}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
