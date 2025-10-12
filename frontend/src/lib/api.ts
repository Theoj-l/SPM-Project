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

export type Project = { id: string; name: string; owner_id: string; cover_url?: string | null; };
export type Task = { id: string; project_id?: string | null; title: string; status: "todo"|"in_progress"|"review"|"done"; assignee_id?: string | null; };

export const ProjectsAPI = {
  list: () => api<Project[]>("/api/projects"),
  create: (name: string, cover_url?: string) =>
    api<Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify({ name, cover_url }),
    }),
};

