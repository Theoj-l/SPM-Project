"use client";

import { useRouter } from "next/navigation";
import { useLoading } from "@/contexts/LoadingContext";
import { useCallback, useEffect, useRef } from "react";
import { usePathname } from "next/navigation";

export function useNavigationWithLoading() {
  const router = useRouter();
  const pathname = usePathname();
  const { setLoading } = useLoading();
  const loadingStartTime = useRef<number | null>(null);
  const targetPath = useRef<string | null>(null);
  const isNavigating = useRef(false);

  // Hide loading when pathname changes to the target path (navigation completed)
  useEffect(() => {
    if (isNavigating.current && targetPath.current) {
      // Check if we've reached the target path
      if (pathname === targetPath.current) {
        // Use a small delay to ensure the page has fully rendered
        setTimeout(() => {
          const elapsed = Date.now() - (loadingStartTime.current || Date.now());
          const minLoadingTime = 1000; // 1 second minimum
          
          if (elapsed >= minLoadingTime) {
            setLoading(false);
            loadingStartTime.current = null;
            targetPath.current = null;
            isNavigating.current = false;
          } else {
            // Wait for the remaining time to reach minimum duration
            const remainingTime = minLoadingTime - elapsed;
            setTimeout(() => {
              setLoading(false);
              loadingStartTime.current = null;
              targetPath.current = null;
              isNavigating.current = false;
            }, remainingTime);
          }
        }, 100); // Small delay to ensure page is rendered
      }
    }
  }, [pathname, setLoading]);

  const navigateWithLoading = useCallback((href: string) => {
    // Only show loading if navigating to a different page
    if (href !== pathname) {
      loadingStartTime.current = Date.now();
      targetPath.current = href;
      isNavigating.current = true;
      setLoading(true);
    }
    router.push(href);
  }, [router, setLoading, pathname]);

  const backWithLoading = useCallback(() => {
    loadingStartTime.current = Date.now();
    targetPath.current = null; // For back navigation, we don't know the target path
    isNavigating.current = true;
    setLoading(true);
    router.back();
    
    // For back navigation, hide loading after a delay since we can't track the target
    setTimeout(() => {
      const elapsed = Date.now() - (loadingStartTime.current || Date.now());
      const minLoadingTime = 1000;
      
      if (elapsed >= minLoadingTime) {
        setLoading(false);
        loadingStartTime.current = null;
        isNavigating.current = false;
      } else {
        const remainingTime = minLoadingTime - elapsed;
        setTimeout(() => {
          setLoading(false);
          loadingStartTime.current = null;
          isNavigating.current = false;
        }, remainingTime);
      }
    }, 200); // Slightly longer delay for back navigation
  }, [router, setLoading]);

  return {
    navigateWithLoading,
    backWithLoading,
    router
  };
}
