"use client";

import { ArrowLeft, Construction } from "lucide-react";
import { useNavigationWithLoading } from "@/hooks/useNavigationWithLoading";
import { Button } from "@/components/ui/button";

interface ComingSoonProps {
  title?: string;
  description?: string;
  showBackButton?: boolean;
}

export default function ComingSoon({
  title = "Coming Soon",
  description = "This feature is being built. Look forward to it!",
  showBackButton = true,
}: ComingSoonProps) {
  const { backWithLoading } = useNavigationWithLoading();

  return (
    <div className="h-screen flex items-center justify-center bg-background overflow-hidden">
      <div className="max-w-md mx-auto text-center px-6">
        {/* Icon */}
        <div className="mb-6">
          <div className="mx-auto w-20 h-20 bg-orange-100 rounded-full flex items-center justify-center">
            <Construction className="h-10 w-10 text-orange-600" />
          </div>
        </div>

        {/* Title */}
        <h1 className="text-3xl font-bold text-gray-900 mb-4">{title}</h1>

        {/* Description */}
        <p className="text-lg text-gray-600 mb-8">{description}</p>

        {/* Back Button */}
        {showBackButton && (
          <Button
            onClick={backWithLoading}
            variant="outline"
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Go Back
          </Button>
        )}
      </div>
    </div>
  );
}
