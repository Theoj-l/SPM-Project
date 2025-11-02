"use client";

import { FormEvent, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import { API_BASE } from "@/lib/api";

export default function ResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<{
    password?: string;
    confirmPassword?: string;
  }>({});
  const [tokenExtracted, setTokenExtracted] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState(true);
  const [currentUrl, setCurrentUrl] = useState<string>("");
  const [currentHash, setCurrentHash] = useState<string>("");

  // Set URL and hash on client side only
  useEffect(() => {
    if (typeof window !== "undefined") {
      setCurrentUrl(window.location.href);
      setCurrentHash(window.location.hash);
    }
  }, []);

  useEffect(() => {
    console.log("🟢 ResetPasswordPage useEffect running");
    // Supabase verification URL redirects to our app with token in hash
    // The format is: redirect_to#access_token=...&type=recovery
    const checkHash = () => {
      try {
        const fullUrl = window.location.href;
        const hash = window.location.hash;
        console.log("=== RESET PASSWORD DEBUG ===");
        console.log("Full URL:", fullUrl);
        console.log("Hash:", hash || "(empty)");
        console.log("Hash length:", hash?.length || 0);
        console.log("Search params:", window.location.search || "(empty)");

        // First check hash (Supabase redirects with hash)
        if (hash && hash.length > 1) {
          // Extract parameters from hash
          const hashParams = new URLSearchParams(hash.substring(1));
          const allParams = Object.fromEntries(hashParams.entries());
          console.log("Reset password - Hash params:", allParams);

          // Check for errors first
          const error = hashParams.get("error");
          const errorCode = hashParams.get("error_code");
          const errorDescription = hashParams.get("error_description");

          if (error) {
            let message = "Invalid or expired reset link.";

            // Prioritize error description if available
            if (errorDescription) {
              try {
                message = decodeURIComponent(
                  errorDescription.replace(/\+/g, " ")
                );
              } catch (e) {
                message = errorDescription.replace(/\+/g, " ");
              }
            } else if (errorCode === "otp_expired") {
              message =
                "This password reset link has expired. Please request a new one.";
            } else if (error === "access_denied") {
              message =
                "Access denied. This reset link may have expired or been invalidated.";
            }

            console.log("Reset password - Error found:", {
              error,
              errorCode,
              errorDescription,
              decodedDescription: errorDescription
                ? decodeURIComponent(errorDescription.replace(/\+/g, " "))
                : null,
              message,
            });
            setErrorMessage(message);
            setIsChecking(false);
            toast.error(message);
            return;
          }

          // Check for valid token
          const accessToken = hashParams.get("access_token");
          const type = hashParams.get("type");

          console.log("Reset password - Token check:", {
            accessToken: accessToken
              ? `${accessToken.substring(0, 20)}...`
              : null,
            type,
            hasToken: !!accessToken,
            isRecovery: type === "recovery",
          });

          if (type === "recovery" && accessToken) {
            // Store token temporarily - we'll send it with the password update
            sessionStorage.setItem("reset_token", accessToken);
            console.log("Reset password - Token stored successfully");
            setTokenExtracted(true);
            setIsChecking(false);
            return;
          }
        }

        // Check search params as fallback (in case Supabase uses query params instead)
        const searchToken = searchParams.get("access_token");
        const searchType = searchParams.get("type");
        const searchError = searchParams.get("error");
        const verifyToken = searchParams.get("token"); // Verification token from Supabase verify URL

        console.log("Reset password - Search params check:", {
          searchToken: searchToken
            ? `${searchToken.substring(0, 20)}...`
            : null,
          searchType,
          searchError,
          verifyToken: verifyToken
            ? `${verifyToken.substring(0, 20)}...`
            : null,
        });

        if (searchError) {
          const errorDescription = searchParams.get("error_description");
          const message = errorDescription
            ? decodeURIComponent(errorDescription)
            : "Invalid or expired reset link. Please request a new password reset.";
          setErrorMessage(message);
          setIsChecking(false);
          toast.error(message);
          return;
        }

        // If we have the verification token from Supabase's verify URL, we need to verify it first
        // This happens when Supabase's redirect doesn't work properly
        if (verifyToken && searchType === "recovery") {
          console.log(
            "Reset password - Found verification token, calling backend to verify"
          );
          setIsChecking(true);

          // Call backend to verify the token and get access token
          fetch(
            `${API_BASE}/api/auth/verify-reset-token?token=${encodeURIComponent(
              verifyToken
            )}`
          )
            .then(async (response) => {
              console.log(
                "Reset password - Verify response:",
                response.status,
                response.url
              );

              // If response redirects, follow it
              if (response.redirected) {
                console.log(
                  "Reset password - Following redirect to:",
                  response.url
                );
                window.location.href = response.url;
                return;
              }

              // If response is JSON with access token
              if (response.ok) {
                const data = await response.json();
                if (data && data.data && data.data.access_token) {
                  sessionStorage.setItem("reset_token", data.data.access_token);
                  setTokenExtracted(true);
                  setIsChecking(false);
                } else if (data && data.access_token) {
                  sessionStorage.setItem("reset_token", data.access_token);
                  setTokenExtracted(true);
                  setIsChecking(false);
                } else {
                  throw new Error("No access token in response");
                }
              } else {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Verification failed");
              }
            })
            .catch((err) => {
              console.error("Reset password - Verification error:", err);
              setErrorMessage(
                "Failed to verify reset token. The link may have expired. Please request a new password reset."
              );
              setIsChecking(false);
              toast.error("Invalid or expired reset link");
            });
          return;
        }

        if (searchType === "recovery" && searchToken) {
          sessionStorage.setItem("reset_token", searchToken);
          setTokenExtracted(true);
          setIsChecking(false);
          return;
        }

        // No token found anywhere yet
        console.log(
          "Reset password - No valid token found in hash or search params"
        );
        // Don't set error immediately - give it time for Supabase redirect to complete
        // The timeouts will check again
        return;
      } catch (error) {
        console.error("❌ Error in checkHash:", error);
        setErrorMessage("Error processing reset link. Please try again.");
        setIsChecking(false);
      }
    };

    // Check immediately
    checkHash();

    // Check multiple times - Supabase redirect might take a moment
    const timeout1 = setTimeout(checkHash, 200);
    const timeout2 = setTimeout(checkHash, 500);
    const timeout3 = setTimeout(checkHash, 1000);
    const timeout4 = setTimeout(() => {
      // Final check - give one more chance before showing error
      checkHash();
      setIsChecking(false);

      // Only show error if we've truly checked everything and found nothing
      if (!tokenExtracted && !errorMessage) {
        console.log(
          "Reset password - Final timeout, no token found after 3 seconds"
        );
        const hash = window.location.hash;
        const hasHash = hash && hash.length > 1;
        console.log(
          "Reset password - Final check - Hash exists:",
          hasHash,
          "Hash:",
          hash
        );

        // Check one more time for token
        if (hasHash) {
          const hashParams = new URLSearchParams(hash.substring(1));
          const accessToken = hashParams.get("access_token");
          const type = hashParams.get("type");

          if (type === "recovery" && accessToken) {
            sessionStorage.setItem("reset_token", accessToken);
            setTokenExtracted(true);
            return;
          }
        }

        // If we get here, no valid token was found
        setErrorMessage(
          "The password reset link appears to be invalid or expired. This may happen if the link was already used or if too much time has passed. Please request a new password reset."
        );
        toast.error("Invalid or expired reset link");
      }
    }, 3000);

    // Listen for hash changes (when Supabase redirects with hash)
    const handleHashChange = () => {
      console.log("Reset password - Hash change detected");
      checkHash();
    };
    window.addEventListener("hashchange", handleHashChange);

    // Also listen for popstate (browser navigation)
    const handlePopState = () => {
      console.log("Reset password - Popstate detected");
      setTimeout(checkHash, 100);
    };
    window.addEventListener("popstate", handlePopState);

    return () => {
      clearTimeout(timeout1);
      clearTimeout(timeout2);
      clearTimeout(timeout3);
      clearTimeout(timeout4);
      window.removeEventListener("hashchange", handleHashChange);
      window.removeEventListener("popstate", handlePopState);
    };
  }, [router, searchParams, isChecking, tokenExtracted]);

  const validate = () => {
    const nextErrors: { password?: string; confirmPassword?: string } = {};
    if (!password) {
      nextErrors.password = "Password is required";
    } else if (password.length < 6) {
      nextErrors.password = "Password must be at least 6 characters";
    }
    if (!confirmPassword) {
      nextErrors.confirmPassword = "Please confirm your password";
    } else if (password !== confirmPassword) {
      nextErrors.confirmPassword = "Passwords do not match";
    }
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const token = sessionStorage.getItem("reset_token");
    if (!token) {
      toast.error(
        "Reset token not found. Please request a new password reset."
      );
      router.push("/login");
      return;
    }

    setSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/api/auth/reset-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          password,
          token,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        toast.error(data.detail || data.message || "Failed to reset password");
        return;
      }

      if (data.success) {
        toast.success("Password reset successfully! You can now login.");
        sessionStorage.removeItem("reset_token");
        router.push("/login");
      } else {
        toast.error("Failed to reset password");
      }
    } catch (err: any) {
      console.error("Password reset error:", err);
      toast.error("Failed to reset password");
    } finally {
      setSubmitting(false);
    }
  };

  if (isChecking) {
    return (
      <div className="min-h-dvh grid place-items-center px-4">
        <div className="w-full max-w-sm rounded-lg border bg-card p-6 shadow-sm">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-sm text-muted-foreground">
              Verifying reset link...
            </p>
            {currentUrl && (
              <>
                <p className="mt-2 text-xs text-muted-foreground">
                  Current URL: {currentUrl.substring(0, 80)}
                  {currentUrl.length > 80 ? "..." : ""}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Hash: {currentHash || "(no hash)"}
                </p>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Only show error if we've explicitly set an error message AND we're not still checking
  // Don't show error if we're still in checking state or if errorMessage is null
  if (!isChecking && errorMessage) {
    return (
      <div className="min-h-dvh grid place-items-center px-4">
        <div className="w-full max-w-sm rounded-lg border bg-card p-6 shadow-sm">
          <div className="mb-6 text-center">
            <h1 className="text-2xl font-semibold text-destructive">
              Reset Link Invalid
            </h1>
            <p className="text-sm text-muted-foreground mt-2">{errorMessage}</p>
          </div>
          <div className="space-y-4">
            <Button onClick={() => router.push("/login")} className="w-full">
              Back to Login
            </Button>
            <div className="text-center text-sm text-muted-foreground">
              <p>Need a new reset link?</p>
              <button
                onClick={() => router.push("/login")}
                className="text-primary hover:underline mt-1"
              >
                Request password reset from login page
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // If we're not checking anymore and no token was extracted and no error message,
  // it means we timed out without finding a token - show error
  if (!isChecking && !tokenExtracted && !errorMessage) {
    return (
      <div className="min-h-dvh grid place-items-center px-4">
        <div className="w-full max-w-sm rounded-lg border bg-card p-6 shadow-sm">
          <div className="mb-6 text-center">
            <h1 className="text-2xl font-semibold text-destructive">
              Reset Link Invalid
            </h1>
            <p className="text-sm text-muted-foreground mt-2">
              This password reset link is invalid or has expired. Please request
              a new password reset.
            </p>
          </div>
          <div className="space-y-4">
            <Button onClick={() => router.push("/login")} className="w-full">
              Back to Login
            </Button>
            <div className="text-center text-sm text-muted-foreground">
              <p>Need a new reset link?</p>
              <button
                onClick={() => router.push("/login")}
                className="text-primary hover:underline mt-1"
              >
                Request password reset from login page
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-dvh grid place-items-center px-4">
      <div className="w-full max-w-sm rounded-lg border bg-card p-6 shadow-sm">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-semibold">Reset Password</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Enter your new password
          </p>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="password" requiredMark>
              New Password
            </Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                error={errors.password}
                inputClassName="pr-10"
              />
              <button
                type="button"
                aria-label={showPassword ? "Hide password" : "Show password"}
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {showPassword ? (
                  <EyeOff className="size-4" />
                ) : (
                  <Eye className="size-4" />
                )}
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword" requiredMark>
              Confirm Password
            </Label>
            <div className="relative">
              <Input
                id="confirmPassword"
                type={showConfirmPassword ? "text" : "password"}
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                error={errors.confirmPassword}
                inputClassName="pr-10"
              />
              <button
                type="button"
                aria-label={
                  showConfirmPassword ? "Hide password" : "Show password"
                }
                onClick={() => setShowConfirmPassword((v) => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {showConfirmPassword ? (
                  <EyeOff className="size-4" />
                ) : (
                  <Eye className="size-4" />
                )}
              </button>
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? "Resetting..." : "Reset Password"}
          </Button>

          <div className="text-center">
            <button
              type="button"
              onClick={() => router.push("/login")}
              className="text-sm text-primary hover:underline"
            >
              Back to login
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
