"use client";

import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function ReportPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  // Check if user has admin role
  const isAdmin = user?.roles?.includes("admin") || false;

  useEffect(() => {
    if (!isLoading && !isAdmin) {
      // Redirect non-admin users to home page
      router.push("/");
    }
  }, [isLoading, isAdmin, router]);

  // Show loading while checking authentication and roles
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-lg font-medium">Loading...</div>
          <div className="text-sm text-muted-foreground mt-2">
            Verifying admin permissions
          </div>
        </div>
      </div>
    );
  }

  // Don't render anything if user is not admin (will redirect)
  if (!isAdmin) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
        <p className="text-muted-foreground">
          View analytics and generate reports
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border bg-card p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Stats</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                Total Projects
              </span>
              <span className="text-2xl font-bold">12</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                Completed Tasks
              </span>
              <span className="text-2xl font-bold">48</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                Pending Items
              </span>
              <span className="text-2xl font-bold">7</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">This Month</span>
              <span className="text-2xl font-bold">23</span>
            </div>
          </div>
        </div>

        <div className="rounded-lg border bg-card p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm">Project Alpha completed</p>
                <p className="text-xs text-muted-foreground">2 hours ago</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm">New task assigned</p>
                <p className="text-xs text-muted-foreground">4 hours ago</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm">Deadline approaching</p>
                <p className="text-xs text-muted-foreground">1 day ago</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-lg border bg-card p-6">
        <h2 className="text-xl font-semibold mb-4">Generate Report</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="p-4 rounded-lg border hover:bg-accent transition-colors">
            <h3 className="font-medium">Weekly Report</h3>
            <p className="text-sm text-muted-foreground">
              Last 7 days activity
            </p>
          </button>
          <button className="p-4 rounded-lg border hover:bg-accent transition-colors">
            <h3 className="font-medium">Monthly Report</h3>
            <p className="text-sm text-muted-foreground">
              This month's summary
            </p>
          </button>
          <button className="p-4 rounded-lg border hover:bg-accent transition-colors">
            <h3 className="font-medium">Custom Report</h3>
            <p className="text-sm text-muted-foreground">Custom date range</p>
          </button>
        </div>
      </div>
    </div>
  );
}
