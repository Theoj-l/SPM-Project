"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useRef,
  ReactNode,
} from "react";
import { useRouter, usePathname } from "next/navigation";
import { toast } from "sonner";

interface User {
  id: string;
  email: string;
  full_name?: string;
  roles?: string[]; // Array of role names (staff, manager, admin)
}

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAuthLoading: boolean;
  isRolesLoaded: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  fetchUserRoles: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [isRolesLoaded, setIsRolesLoaded] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  const isAuthenticated = !!user;

  // Refs for inactivity timer
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const warningTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastActivityRef = useRef<number>(Date.now());

  // Check for existing authentication on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  // Handle user activity events
  useEffect(() => {
    if (!isAuthenticated) {
      stopInactivityTimer();
      return;
    }

    // Initialize timer when user is authenticated
    resetInactivityTimer();

    // Event handler for user activity
    const handleActivity = () => {
      resetInactivityTimer();
    };

    // Events to listen for
    const events = [
      "mousedown",
      "mousemove",
      "keypress",
      "scroll",
      "touchstart",
      "click",
      "keydown",
    ];

    // Add event listeners
    events.forEach((event) => {
      document.addEventListener(event, handleActivity, true);
    });

    // Cleanup function
    return () => {
      events.forEach((event) => {
        document.removeEventListener(event, handleActivity, true);
      });
      stopInactivityTimer();
    };
  }, [isAuthenticated]);

  // Redirect logic based on authentication status
  useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated && pathname === "/login") {
        // User is authenticated but on login page, redirect to home
        router.push("/");
      } else if (!isAuthenticated && pathname !== "/login") {
        // User is not authenticated and not on login page, redirect to login
        router.push("/login");
      }
    }
  }, [isAuthenticated, isLoading, pathname, router]);

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setIsLoading(false);
        return;
      }

      // Verify token with backend
      const response = await fetch("http://localhost:5000/api/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data) {
          setUser(data.data);
          // Fetch user roles after setting user data
          await fetchUserRoles();
        } else {
          // Invalid token, clear storage
          console.log("Invalid token response, clearing auth data");
          clearAuthData();
        }
      } else {
        // Token invalid or expired
        console.log(
          `Token verification failed with status ${response.status}, clearing auth data`
        );
        clearAuthData();
      }
    } catch (error) {
      console.error("Auth check failed:", error);
      clearAuthData();
    } finally {
      setIsAuthLoading(false);
      setIsLoading(false);
    }
  };

  const clearAuthData = () => {
    console.log("Clearing authentication data");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    setUser(null);
    setIsRolesLoaded(false);
    setIsAuthLoading(false);
  };

  const fetchUserRoles = async (): Promise<boolean> => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        return false;
      }

      const response = await fetch(
        "http://localhost:5000/api/auth/user-roles",
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data) {
          // Update user with roles data
          setUser((prevUser) => {
            if (prevUser) {
              const updatedUser = {
                ...prevUser,
                ...data.data,
              };
              // Update localStorage with new user data
              localStorage.setItem("user", JSON.stringify(updatedUser));
              return updatedUser;
            }
            return prevUser;
          });
          setIsRolesLoaded(true);
          return true;
        }
      }

      console.log(`Failed to fetch user roles: ${response.status}`);
      return false;
    } catch (error) {
      console.error("Fetch user roles error:", error);
      return false;
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await fetch("http://localhost:5000/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage =
          errorData.detail || errorData.message || "Login failed";

        if (response.status === 401) {
          toast.error("Invalid email or password");
        } else if (response.status === 404) {
          toast.error("Email not found. Please contact administrator");
        } else {
          toast.error(errorMessage);
        }
        return false;
      }

      const data = await response.json();

      if (data.success && data.data) {
        const { access_token, refresh_token, user: userData } = data.data;

        // Store tokens and user data
        localStorage.setItem("access_token", access_token);
        localStorage.setItem("refresh_token", refresh_token);
        localStorage.setItem("user", JSON.stringify(userData));

        setUser(userData);

        // Fetch user roles after successful login
        const rolesFetched = await fetchUserRoles();
        if (rolesFetched) {
          setIsRolesLoaded(true);
        }

        toast.success("Login successful");
        return true;
      } else {
        toast.error("Login failed");
        return false;
      }
    } catch (error: any) {
      console.error("Login error:", error);
      toast.error(error?.message || "Login failed");
      return false;
    }
  };

  const logout = () => {
    clearAuthData();
    toast.success("Logged out successfully");
    // Don't redirect here - let the logout page handle the redirect
  };

  // Auto-logout after 15 minutes of inactivity
  const handleAutoLogout = () => {
    if (isAuthenticated) {
      toast.warning("You have been automatically logged out due to inactivity");
      logout();
    }
  };

  // Warning toast 1 minute before auto-logout
  const handleWarning = () => {
    if (isAuthenticated) {
      toast.warning(
        "In 1 minute, auto logout will be triggered if no activity is detected",
        {
          duration: 60000, // Show for 1 minute
        }
      );
    }
  };

  // Reset inactivity timer
  const resetInactivityTimer = () => {
    lastActivityRef.current = Date.now();

    // Clear existing timeouts
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    if (warningTimeoutRef.current) {
      clearTimeout(warningTimeoutRef.current);
    }

    // Set warning timeout (1 minute before main timeout)
    warningTimeoutRef.current = setTimeout(() => {
      handleWarning();
    }, 14 * 60 * 1000); // 14 minutes

    // Set main timeout (15 minutes)
    timeoutRef.current = setTimeout(() => {
      handleAutoLogout();
    }, 15 * 60 * 1000); // 15 minutes
  };

  // Stop inactivity timer
  const stopInactivityTimer = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (warningTimeoutRef.current) {
      clearTimeout(warningTimeoutRef.current);
      warningTimeoutRef.current = null;
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      const refreshTokenValue = localStorage.getItem("refresh_token");
      if (!refreshTokenValue) {
        return false;
      }

      const response = await fetch("http://localhost:5000/api/auth/refresh", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data) {
          const { access_token, refresh_token: newRefreshToken } = data.data;
          localStorage.setItem("access_token", access_token);
          localStorage.setItem("refresh_token", newRefreshToken);
          return true;
        }
      }

      // Refresh failed, logout user
      clearAuthData();
      return false;
    } catch (error) {
      console.error("Token refresh failed:", error);
      clearAuthData();
      return false;
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading: isLoading || !isRolesLoaded,
    isAuthLoading,
    isRolesLoaded,
    login,
    logout,
    refreshToken,
    fetchUserRoles,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
