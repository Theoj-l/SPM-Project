/**
 * Authentication utility functions
 * These can be used in the browser console for debugging
 */

export const clearAuthData = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
  console.log("Authentication data cleared from localStorage");
};

export const checkAuthData = () => {
  const token = localStorage.getItem("access_token");
  const refreshToken = localStorage.getItem("refresh_token");
  const user = localStorage.getItem("user");
  
  console.log("Current auth data:");
  console.log("Access token:", token ? `${token.substring(0, 20)}...` : "None");
  console.log("Refresh token:", refreshToken ? `${refreshToken.substring(0, 20)}...` : "None");
  console.log("User:", user ? JSON.parse(user) : "None");
  if (user) {
    const userData = JSON.parse(user);
    console.log("User roles:", userData.roles || "None");
    console.log("User role names:", userData.role_names || "None");
  }
};

// Make functions available globally for console debugging
if (typeof window !== 'undefined') {
  (window as any).clearAuthData = clearAuthData;
  (window as any).checkAuthData = checkAuthData;
}
