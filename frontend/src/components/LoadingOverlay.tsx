"use client";

import { useLoading } from "@/contexts/LoadingContext";

export default function LoadingOverlay() {
  const { isLoading } = useLoading();

  if (!isLoading) return null;

  return (
    <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
        <div className="text-lg font-medium">Loading...</div>
        <div className="text-sm text-muted-foreground mt-2">
          Please wait while we load the page
        </div>
      </div>
    </div>
  );
}
