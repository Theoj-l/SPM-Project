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

export type Project = { id: string; name: string; owner_id: string; owner_display_name?: string; cover_url?: string | null; user_role?: string; status?: "active" | "archived"; };
export type Task = { id: string; project_id?: string | null; title: string; description?: string; status: "todo"|"in_progress"|"completed"|"blocked"; due_date?: string; notes?: string; assignee_ids?: string[]; assignee_names?: string[]; assigned?: string[]; type?: "active"|"archived"; tags?: string[]; created_at?: string; };
export type User = { id: string; email: string; display_name?: string; roles: string[]; };
export type ProjectMember = { project_id: string; user_id: string; role: string; user_email?: string; user_display_name?: string; };

export const ProjectsAPI = {
  list: (includeArchived: boolean = false) => 
    api<Project[]>(`/api/projects${includeArchived ? '?include_archived=true' : ''}`),
  getById: (projectId: string) => api<Project>(`/api/projects/${projectId}`),
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
  getArchived: () => api<Project[]>("/api/projects/archived"),
  archive: (projectId: string) =>
    api(`/api/projects/${projectId}/archive`, {
      method: "PATCH",
    }),
  restore: (projectId: string) =>
    api(`/api/projects/${projectId}/restore`, {
      method: "PATCH",
    }),
};

export const UsersAPI = {
  list: () => api<User[]>("/api/users"),
  search: (query: string) => api<User[]>(`/api/users/search?query=${encodeURIComponent(query)}`),
};

export const TasksAPI = {
  list: (projectId: string, includeArchived: boolean = false) => 
    api<Task[]>(`/api/projects/${projectId}/tasks${includeArchived ? '?include_archived=true' : ''}`),
  getById: (taskId: string) => api<Task>(`/api/tasks/${taskId}`),
  create: (projectId: string, taskData: {
    title: string;
    description?: string;
    due_date?: string;
    notes?: string;
    assignee_ids?: string[];
    status?: "todo" | "in_progress" | "completed" | "blocked";
  }) =>
    api<Task>(`/api/projects/${projectId}/tasks`, {
      method: "POST",
      body: JSON.stringify(taskData),
    }),
  update: (taskId: string, updates: Partial<Task>) =>
    api<Task>(`/api/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(updates),
    }),
  updateAssignees: (taskId: string, assignee_ids: string[]) =>
    api<Task>(`/api/tasks/${taskId}/assignees`, {
      method: "PATCH",
      body: JSON.stringify({ assignee_ids }),
    }),
  delete: (taskId: string) =>
    api(`/api/tasks/${taskId}`, {
      method: "DELETE",
    }),
  archive: (taskId: string) =>
    api<Task>(`/api/tasks/${taskId}/archive`, {
      method: "PATCH",
    }),
  restore: (taskId: string) =>
    api<Task>(`/api/tasks/${taskId}/restore`, {
      method: "PATCH",
    }),
};

// Comment types and API
export type Comment = {
  id: string;
  task_id: string;
  user_id: string;
  parent_comment_id?: string;
  content: string;
  created_at: string;
  user_email?: string;
  user_display_name?: string;
  replies?: Comment[];
};

export const CommentsAPI = {
  list: (taskId: string) => api<Comment[]>(`/api/tasks/${taskId}/comments`),
  create: (taskId: string, content: string, parentCommentId?: string) =>
    api<Comment>(`/api/tasks/${taskId}/comments`, {
      method: "POST",
      body: JSON.stringify({ 
        content, 
        task_id: taskId, 
        parent_comment_id: parentCommentId 
      }),
    }),
  update: (commentId: string, content: string) =>
    api<Comment>(`/api/comments/${commentId}`, {
      method: "PUT",
      body: JSON.stringify({ content }),
    }),
  delete: (commentId: string) =>
    api(`/api/tasks/comments/${commentId}`, {
      method: "DELETE",
    }),
};

// Sub-task types and API
export type SubTask = {
  id: string;
  title: string;
  description?: string;
  parent_task_id: string;
  status: "todo" | "in_progress" | "completed" | "blocked";
  assignee_ids?: string[];
  assignee_names?: string[];
  tags?: string[];
  created_at?: string;
};

export const SubTasksAPI = {
  list: (taskId: string) => api<SubTask[]>(`/api/tasks/${taskId}/subtasks`),
  getById: (subtaskId: string) => api<SubTask>(`/api/tasks/subtasks/${subtaskId}`),
  create: (taskId: string, taskData: {
    title: string;
    description?: string;
    status?: "todo" | "in_progress" | "completed" | "blocked";
    assignee_ids?: string[];
    tags?: string[];
    due_date?: string;
    notes?: string;
  }) =>
    api<SubTask>(`/api/tasks/${taskId}/subtasks`, {
      method: "POST",
      body: JSON.stringify({ ...taskData, parent_task_id: taskId }),
    }),
  update: (subtaskId: string, updates: Partial<SubTask>) =>
    api<SubTask>(`/api/tasks/subtasks/${subtaskId}`, {
      method: "PATCH",
      body: JSON.stringify(updates),
    }),
  delete: (subtaskId: string) =>
    api(`/api/tasks/subtasks/${subtaskId}`, {
      method: "DELETE",
    }),
};

// File types and API
export type TaskFile = {
  id: string;
  filename: string;
  original_filename: string;
  content_type: string;
  file_size: number;
  task_id: string;
  uploaded_by: string;
  created_at: string;
  download_url?: string;
  uploader_email?: string;
  uploader_display_name?: string;
};

export const FilesAPI = {
  list: (taskId: string) => api<TaskFile[]>(`/api/tasks/${taskId}/files`),
  upload: (taskId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api<TaskFile>(`/api/tasks/${taskId}/files`, {
      method: "POST",
      body: formData,
    });
  },
  delete: (fileId: string) =>
    api(`/api/tasks/files/${fileId}`, {
      method: "DELETE",
    }),
};

