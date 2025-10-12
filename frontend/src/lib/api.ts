export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:5000";

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem('access_token');
  
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token && { "Authorization": `Bearer ${token}` }),
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  
  if (!res.ok) {
    // If unauthorized, clear the token and redirect to login
    if (res.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    
    const msg = await res.text();
    throw new Error(msg || res.statusText);
  }
  return res.json() as Promise<T>;
}

export type Project = { id: string; name: string; owner_id: string; owner_display_name?: string; cover_url?: string | null; user_role?: string; };
export type Task = { id: string; project_id?: string | null; title: string; status: "todo"|"in_progress"|"review"|"done"; assignee_id?: string | null; };
export type User = { id: string; email: string; display_name?: string; roles: string[]; };
export type ProjectMember = { project_id: string; user_id: string; role: string; user_email?: string; user_display_name?: string; };

export const ProjectsAPI = {
  list: () => api<Project[]>("/api/projects"),
  create: (name: string, cover_url?: string) =>
    api<Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify({ name, cover_url }),
    }),
  delete: (projectId: string) =>
    api(`/api/projects/${projectId}`, {
      method: "DELETE",
    }),
  getMembers: (projectId: string) => api<ProjectMember[]>(`/api/projects/${projectId}/members`),
  addMember: (projectId: string, email: string, role: string = "staff") =>
    api<ProjectMember>(`/api/projects/${projectId}/add_member`, {
      method: "POST",
      body: JSON.stringify({ email, role }),
    }),
  updateMemberRole: (projectId: string, memberId: string, newRole: string) =>
    api(`/api/projects/${projectId}/members/${memberId}/role?new_role=${newRole}`, {
      method: "PATCH",
    }),
  removeMember: (projectId: string, memberId: string) =>
    api(`/api/projects/${projectId}/members/${memberId}`, {
      method: "DELETE",
    }),
};

export const UsersAPI = {
  list: () => api<User[]>("/api/users"),
  search: (query: string) => api<User[]>(`/api/users/search?query=${encodeURIComponent(query)}`),
};

