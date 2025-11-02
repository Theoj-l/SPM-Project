"use client";

import { ReactNode, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { usePathname, useRouter } from "next/navigation";

interface ProtectedRouteProps {
  children: ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, isAuthLoading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  // Handle redirects for authenticated users trying to access login
  useEffect(() => {
    if (!isAuthLoading && isAuthenticated && pathname === "/login") {
      router.replace("/logout");
    }
  }, [isAuthLoading, isAuthenticated, pathname, router]);

  // For login and reset-password pages, show immediately without any loading
  if (pathname === "/login" || pathname === "/reset-password") {
    // If user is authenticated, redirect to logout (handled by useEffect)
    // Otherwise, show page immediately
    return <>{children}</>;
  }

  // For all other pages, wait for both authentication and roles
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  // If user is not authenticated and trying to access logout page, redirect to login
  if (!isAuthenticated && pathname === "/logout") {
    return null; // The logout page will handle the redirect to login
  }

  // If user is not authenticated and trying to access any other page, redirect to login
  if (!isAuthenticated) {
    return null; // The AuthContext will handle the redirect to login
  }

  // User is authenticated and accessing a protected page, render the content
  return <>{children}</>;
}
