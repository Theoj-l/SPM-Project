"use client";

import { useAuth } from "@/contexts/AuthContext";
import { hasRole, hasAnyRole, hasMinimumRole, ROLES } from "@/utils/role-utils";

interface RoleBasedComponentProps {
  children: React.ReactNode;
  requiredRoles?: number[];
  requireAll?: boolean;
  minimumRole?: number;
  fallback?: React.ReactNode;
}

/**
 * Component that renders children based on user roles
 */
export default function RoleBasedComponent({
  children,
  requiredRoles,
  requireAll = false,
  minimumRole,
  fallback = null,
}: RoleBasedComponentProps) {
  const { user } = useAuth();

  // Check if user has access
  let hasAccess = true;

  if (requiredRoles && requiredRoles.length > 0) {
    if (requireAll) {
      hasAccess = requiredRoles.every((role) => hasRole(user, role));
    } else {
      hasAccess = hasAnyRole(user, requiredRoles);
    }
  }

  if (minimumRole !== undefined) {
    hasAccess = hasAccess && hasMinimumRole(user, minimumRole);
  }

  return hasAccess ? <>{children}</> : <>{fallback}</>;
}

/**
 * Example usage components
 */
export function AdminOnlyComponent({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RoleBasedComponent
      requiredRoles={[ROLES.ADMIN]}
      fallback={
        <div className="text-muted-foreground">Admin access required</div>
      }
    >
      {children}
    </RoleBasedComponent>
  );
}

export function ManagerOrAdminComponent({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RoleBasedComponent
      requiredRoles={[ROLES.MANAGER, ROLES.ADMIN]}
      fallback={
        <div className="text-muted-foreground">
          Manager or Admin access required
        </div>
      }
    >
      {children}
    </RoleBasedComponent>
  );
}

export function StaffOrHigherComponent({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RoleBasedComponent
      minimumRole={ROLES.STAFF}
      fallback={
        <div className="text-muted-foreground">Staff access required</div>
      }
    >
      {children}
    </RoleBasedComponent>
  );
}
