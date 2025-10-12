"use client";

import { useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";

export default function LogoutPage() {
  const { logout, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // If user is not authenticated, redirect to login
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
      return;
    }

    // If user is authenticated, perform logout
    if (!isLoading && isAuthenticated) {
      // Perform logout logic
      logout();

      // Optionally call backend logout endpoint for server-side cleanup
      // This is commented out since the current backend doesn't have proper logout implementation
      // fetch('http://localhost:5000/api/auth/logout', {
      //   method: 'POST',
      //   headers: {
      //     'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      //     'Content-Type': 'application/json',
      //   },
      // }).catch(console.error);

      // Redirect to login after a short delay to show logout message
      setTimeout(() => {
        router.replace("/login");
      }, 1500);
    }
  }, [isAuthenticated, isLoading, logout, router]);

  // Show loading spinner while checking authentication or performing logout
  if (isLoading) {
    return (
      <div className="min-h-dvh grid place-items-center px-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Checking authentication...</p>
        </div>
      </div>
    );
  }

  // Show logout message while processing
  return (
    <div className="min-h-dvh grid place-items-center px-4">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
        <h1 className="text-2xl font-semibold mb-2">Logging out...</h1>
        <p className="text-muted-foreground">
          Please wait while we sign you out.
        </p>
      </div>
    </div>
  );
}
