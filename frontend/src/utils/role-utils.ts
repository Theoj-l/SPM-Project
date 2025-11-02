/**
 * Role-based access control utilities
 */

// Role constants
export const ROLES = {
  STAFF: 1,
  MANAGER: 2,
  ADMIN: 3,
} as const;

export const ROLE_NAMES = {
  [ROLES.STAFF]: "staff",
  [ROLES.MANAGER]: "manager", 
  [ROLES.ADMIN]: "admin",
} as const;

export type RoleId = typeof ROLES[keyof typeof ROLES];
export type RoleName = typeof ROLE_NAMES[keyof typeof ROLE_NAMES];

// User interface for role checking
export interface UserWithRoles {
  roles?: string[];
}

/**
 * Check if user has a specific role
 */
export const hasRole = (user: UserWithRoles | null, roleName: string): boolean => {
  if (!user || !user.roles) {
    return false;
  }
  return user.roles.includes(roleName);
};

/**
 * Check if user has any of the specified roles
 */
export const hasAnyRole = (user: UserWithRoles | null, roleNames: string[]): boolean => {
  if (!user || !user.roles) {
    return false;
  }
  return roleNames.some(roleName => user.roles!.includes(roleName));
};

/**
 * Check if user has all of the specified roles
 */
export const hasAllRoles = (user: UserWithRoles | null, roleNames: string[]): boolean => {
  if (!user || !user.roles) {
    return false;
  }
  return roleNames.every(roleName => user.roles!.includes(roleName));
};

/**
 * Check if user has minimum role level
 */
export const hasMinimumRole = (user: UserWithRoles | null, minimumRole: string): boolean => {
  if (!user || !user.roles || user.roles.length === 0) {
    return false;
  }
  const roleHierarchy = ["staff", "manager", "admin"];
  const userMaxLevel = Math.max(...user.roles.map(role => roleHierarchy.indexOf(role)));
  const minLevel = roleHierarchy.indexOf(minimumRole);
  return userMaxLevel >= minLevel;
};

/**
 * Check if user is staff or higher
 */
export const isStaff = (user: UserWithRoles | null): boolean => {
  return hasMinimumRole(user, "staff");
};

/**
 * Check if user is manager or higher
 */
export const isManager = (user: UserWithRoles | null): boolean => {
  return hasRole(user, "manager");
};

/**
 * Check if user has manager role specifically (not admin)
 */
export const hasManagerRole = (user: UserWithRoles | null): boolean => {
  return hasRole(user, "manager");
};

/**
 * Check if user is admin
 */
export const isAdmin = (user: UserWithRoles | null): boolean => {
  return hasRole(user, "admin");
};

/**
 * Get role name by ID
 */
export const getRoleName = (roleId: RoleId): RoleName => {
  return ROLE_NAMES[roleId] || "unknown";
};

/**
 * Get all role names for a user
 */
export const getUserRoleNames = (user: UserWithRoles | null): string[] => {
  if (!user || !user.roles) {
    return [];
  }
  return user.roles;
};

/**
 * Get highest role name for a user
 */
export const getHighestRoleName = (user: UserWithRoles | null): string => {
  if (!user || !user.roles || user.roles.length === 0) {
    return "staff";
  }
  const roleHierarchy = ["staff", "manager", "admin"];
  const userMaxLevel = Math.max(...user.roles.map(role => roleHierarchy.indexOf(role)));
  return roleHierarchy[userMaxLevel] || "staff";
};

/**
 * Check if user can access a feature based on role requirements
 */
export const canAccessFeature = (
  user: UserWithRoles | null,
  requiredRoles: string[],
  requireAll: boolean = false
): boolean => {
  if (!user || !user.roles) {
    return false;
  }
  
  if (requireAll) {
    return hasAllRoles(user, requiredRoles);
  } else {
    return hasAnyRole(user, requiredRoles);
  }
};

/**
 * Check if admin user can manage projects (has manager or staff role)
 * Admin alone is read-only, need manager or staff for management
 */
export const canAdminManage = (user: UserWithRoles | null): boolean => {
  return isAdmin(user) && (hasRole(user, "manager") || hasRole(user, "staff"));
};


// Make functions available globally for console debugging
if (typeof window !== 'undefined') {
  (window as any).ROLES = ROLES;
  (window as any).ROLE_NAMES = ROLE_NAMES;
  (window as any).hasRole = hasRole;
  (window as any).hasAnyRole = hasAnyRole;
  (window as any).hasAllRoles = hasAllRoles;
  (window as any).hasMinimumRole = hasMinimumRole;
  (window as any).isStaff = isStaff;
  (window as any).isManager = isManager;
  (window as any).isAdmin = isAdmin;
  (window as any).getRoleName = getRoleName;
  (window as any).getUserRoleNames = getUserRoleNames;
  (window as any).getHighestRoleName = getHighestRoleName;
  (window as any).canAccessFeature = canAccessFeature;
}
