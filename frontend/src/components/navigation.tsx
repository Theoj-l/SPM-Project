"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import {
  Home,
  User,
  Settings,
  LogOut,
  Menu,
  X,
  FileSearch,
  ClipboardClock,
  Bell,
  Archive,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface NavigationProps {
  children: React.ReactNode;
}

interface NavigationItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  onClick?: () => void;
}

/**
 * Combined Navigation Component
 * - Contains all sidebar functionality in one component
 * - Handles navigation state, mobile responsiveness, and routing
 * - Includes sidebar UI components inline
 */
export default function Navigation({ children }: NavigationProps) {
  const [isCollapsed, setIsCollapsed] = useState(true);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const pathname = usePathname();
  const { user, isLoading } = useAuth();

  // Don't show sidebar on login or logout pages
  if (pathname === "/login" || pathname === "/logout") {
    return <div className="min-h-screen bg-background">{children}</div>;
  }

  // Show loading screen while authentication and roles are being loaded
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg font-medium">Loading...</div>
          <div className="text-sm text-muted-foreground mt-2">
            Fetching user roles and permissions
          </div>
        </div>
      </div>
    );
  }

  // Check if user has admin role
  const isAdmin = user?.roles?.includes("admin") || false;

  const mainNavigationItems = [
    {
      title: "Main",
      items: [
        {
          href: "/",
          label: "Workspace",
          icon: <Home className="h-4 w-4" />,
        },
        {
          href: "/calendar",
          label: "Calendar",
          icon: <ClipboardClock className="h-4 w-4" />,
        },
        // Only show Reports for admin users
        ...(isAdmin
          ? [
              {
                href: "/report",
                label: "Reports",
                icon: <FileSearch className="h-4 w-4" />,
              },
            ]
          : []),
        {
          href: "/notifications",
          label: "Notifications",
          icon: <Bell className="h-4 w-4" />,
        },
        {
          href: "/archived",
          label: "Archived",
          icon: <Archive className="h-4 w-4" />,
        },
      ] as NavigationItem[],
    },
  ];

  const accountNavigationItems = [
    {
      title: "Account",
      items: [
        {
          href: "/profile",
          label: "Profile",
          icon: <User className="h-4 w-4" />,
        },
        {
          href: "/settings",
          label: "Settings",
          icon: <Settings className="h-4 w-4" />,
        },
        {
          href: "/logout",
          label: "Logout",
          icon: <LogOut className="h-4 w-4" />,
        },
      ] as NavigationItem[],
    },
  ];

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }
    return pathname.startsWith(href);
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`
          fixed inset-y-0 left-0 z-50 w-64 transform transition-all duration-300 ease-in-out lg:relative lg:translate-x-0
          ${isMobileOpen ? "translate-x-0" : "-translate-x-full"}
          ${isCollapsed ? "lg:w-10" : "lg:w-64"}
        `}
      >
        {/* Sidebar Container */}
        <div
          className={cn(
            // Base styles: vertical flex layout with border and background
            "flex h-full flex-col border-r bg-background transition-all duration-300 ease-in-out",
            // Dynamic width: 14 (56px) when collapsed, 60 (240px) when expanded
            isCollapsed ? "w-12" : "w-60"
          )}
        >
          {/* Sidebar Header: Contains title and toggle button */}
          <div
            className={cn(
              // Base header styles: fixed height with border and smooth transitions
              "flex h-14 items-center border-b transition-all duration-300 ease-in-out",
              // Layout: centered when collapsed, space-between when expanded
              isCollapsed ? "justify-center" : "justify-between px-4"
            )}
          >
            {/* Sidebar Logo: Fades out and collapses when sidebar is collapsed */}
            <div
              className={cn(
                "flex items-center transition-all duration-300 ease-in-out",
                // Hide logo when collapsed: opacity 0, width 0, overflow hidden
                isCollapsed ? "opacity-0 w-0 overflow-hidden" : "opacity-100"
              )}
            >
              <Image
                src="/logo.svg"
                alt="Jite Logo"
                width={32}
                height={32}
                className="mr-2"
              />
              <h2 className="text-lg font-semibold">Jite</h2>
            </div>

            {/* Toggle Button: Hamburger when collapsed, X when expanded */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="h-8 w-8"
            >
              {isCollapsed ? (
                <Menu className="h-4 w-4" />
              ) : (
                <X className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Main Navigation Items - Scrollable */}
          <div className="flex-1 overflow-y-auto p-2">
            {mainNavigationItems.map((group, groupIndex) => (
              <div key={groupIndex} className="space-y-1">
                {/* Group Title: Only shown when expanded, fades out when collapsed */}
                {group.title && (
                  <div
                    className={cn(
                      // Base title styles: small, uppercase, muted color with smooth transitions
                      "px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider transition-all duration-300 ease-in-out",
                      // Hide title when collapsed: opacity 0, height 0, overflow hidden, no padding
                      isCollapsed
                        ? "opacity-0 h-0 overflow-hidden py-0"
                        : "opacity-100 py-2"
                    )}
                  >
                    {group.title}
                  </div>
                )}

                {/* Group Items: Always visible, consistent spacing */}
                {group.items.map((item) => (
                  <Link key={item.href} href={item.href}>
                    <div
                      className={cn(
                        // Base item styles: flex layout with hover effects and smooth transitions
                        "flex items-center rounded-md py-2 text-sm font-medium transition-all duration-300 ease-in-out hover:bg-accent hover:text-accent-foreground cursor-pointer",
                        // Gap: only when expanded, no gap when collapsed
                        isCollapsed ? "" : "gap-3",
                        // Active state: highlighted background and text color
                        isActive(item.href) &&
                          "bg-accent text-accent-foreground",
                        // Padding: no horizontal padding when collapsed, normal padding when expanded
                        isCollapsed ? "justify-center" : "px-3"
                      )}
                      onClick={() => setIsMobileOpen(false)}
                    >
                      {/* Icon Container: Always visible, flex-shrink-0 prevents icon from shrinking */}
                      <div className="flex-shrink-0">{item.icon}</div>

                      {/* Text Label: Fades out and collapses when sidebar is collapsed */}
                      <span
                        className={cn(
                          "transition-all duration-300 ease-in-out",
                          // Hide text when collapsed: opacity 0, width 0, overflow hidden
                          isCollapsed
                            ? "opacity-0 w-0 overflow-hidden"
                            : "opacity-100"
                        )}
                      >
                        {item.label}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            ))}
          </div>

          {/* Account Navigation Items - Fixed at bottom, no scroll */}
          <div className="p-2">
            {accountNavigationItems.map((group, groupIndex) => (
              <div key={groupIndex} className="space-y-1">
                {/* Group Title: Only shown when expanded, fades out when collapsed */}
                {group.title && (
                  <div
                    className={cn(
                      // Base title styles: small, uppercase, muted color with smooth transitions
                      "px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider transition-all duration-300 ease-in-out",
                      // Hide title when collapsed: opacity 0, height 0, overflow hidden, no padding
                      isCollapsed
                        ? "opacity-0 h-0 overflow-hidden py-0"
                        : "opacity-100 py-2"
                    )}
                  >
                    {group.title}
                  </div>
                )}

                {/* Group Items: Always visible, consistent spacing */}
                {group.items.map((item) => {
                  const handleClick = () => {
                    setIsMobileOpen(false);
                    if (item.onClick) {
                      item.onClick();
                    }
                  };

                  const content = (
                    <div
                      className={cn(
                        // Base item styles: flex layout with hover effects and smooth transitions
                        "flex items-center rounded-md py-2 text-sm font-medium transition-all duration-300 ease-in-out hover:bg-accent hover:text-accent-foreground cursor-pointer",
                        // Gap: only when expanded, no gap when collapsed
                        isCollapsed ? "" : "gap-3",
                        // Active state: highlighted background and text color
                        isActive(item.href) &&
                          "bg-accent text-accent-foreground",
                        // Padding: no horizontal padding when collapsed, normal padding when expanded
                        isCollapsed ? "justify-center" : "px-3"
                      )}
                      onClick={handleClick}
                    >
                      {/* Icon Container: Always visible, flex-shrink-0 prevents icon from shrinking */}
                      <div className="flex-shrink-0">{item.icon}</div>

                      {/* Text Label: Fades out and collapses when sidebar is collapsed */}
                      <span
                        className={cn(
                          "transition-all duration-300 ease-in-out",
                          // Hide text when collapsed: opacity 0, width 0, overflow hidden
                          isCollapsed
                            ? "opacity-0 w-0 overflow-hidden"
                            : "opacity-100"
                        )}
                      >
                        {item.label}
                      </span>
                    </div>
                  );

                  return item.href === "#" ? (
                    <div key={item.label}>{content}</div>
                  ) : (
                    <Link key={item.href} href={item.href}>
                      {content}
                    </Link>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Mobile header */}
        <div className="flex h-14 items-center justify-between border-b bg-background px-4 lg:hidden">
          <h1 className="text-lg font-semibold">SPM Project</h1>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsMobileOpen(!isMobileOpen)}
          >
            {isMobileOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </Button>
        </div>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">{children}</main>
      </div>
    </div>
  );
}
