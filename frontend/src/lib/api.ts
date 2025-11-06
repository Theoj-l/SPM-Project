export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:5000";

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem('access_token');
  
  // Don't set Content-Type for FormData - browser sets it automatically with boundary
  const isFormData = init?.body instanceof FormData;
  const headers: HeadersInit = {
    ...(token && { "Authorization": `Bearer ${token}` }),
    ...(init?.headers || {}),
  };
  
  // Only set Content-Type if not FormData and not already set in init.headers
  if (!isFormData && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
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
export type Task = { id: string; project_id?: string | null; title: string; description?: string; status: "todo"|"in_progress"|"completed"|"blocked"; due_date?: string; notes?: string; assignee_ids?: string[]; assignee_names?: string[]; assigned?: string[]; type?: "active"|"archived"; tags?: string[]; priority?: number; created_at?: string; };
export type User = { id: string; email: string; display_name?: string; roles: string[]; };
export type ProjectMember = { project_id: string; user_id: string; role: string; user_email?: string; user_display_name?: string; };

export const ProjectsAPI = {
  // Get all projects, optionally including archived ones
  list: (includeArchived: boolean = false) => 
    api<Project[]>(`/api/projects${includeArchived ? '?include_archived=true' : ''}`),
  // Get all projects in the system (admin only)
  listAll: (includeArchived: boolean = false) => 
    api<Project[]>(`/api/projects/admin/all${includeArchived ? '?include_archived=true' : ''}`),
  // Get a specific project by ID
  getById: (projectId: string) => api<Project>(`/api/projects/${projectId}`),
  // Create a new project with name and optional cover image
  create: (name: string, cover_url?: string) =>
    api<Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify({ name, cover_url }),
    }),
  // Delete a project permanently
  delete: (projectId: string) =>
    api(`/api/projects/${projectId}`, {
      method: "DELETE",
    }),
  // Get all members of a project
  getMembers: (projectId: string) => api<ProjectMember[]>(`/api/projects/${projectId}/members`),
  // Add a new member to a project by email
  addMember: (projectId: string, email: string, role: string = "staff") =>
    api<ProjectMember>(`/api/projects/${projectId}/add_member`, {
      method: "POST",
      body: JSON.stringify({ email, role }),
    }),
  // Update a project member's role
  updateMemberRole: (projectId: string, memberId: string, newRole: string) =>
    api(`/api/projects/${projectId}/members/${memberId}/role?new_role=${newRole}`, {
      method: "PATCH",
    }),
  // Remove a member from a project
  removeMember: (projectId: string, memberId: string) =>
    api(`/api/projects/${projectId}/members/${memberId}`, {
      method: "DELETE",
    }),
  // Get all archived projects
  getArchived: () => api<Project[]>("/api/projects/archived"),
  // Archive a project (soft delete)
  archive: (projectId: string) =>
    api(`/api/projects/${projectId}/archive`, {
      method: "PATCH",
    }),
  // Restore an archived project
  restore: (projectId: string) =>
    api(`/api/projects/${projectId}/restore`, {
      method: "PATCH",
    }),
  // Get projects for a specific user
  getUserProjects: (userId: string, includeArchived: boolean = false) =>
    api<Project[]>(`/api/projects/user/${userId}${includeArchived ? '?include_archived=true' : ''}`),
};

export const UsersAPI = {
  // Get all users in the system
  list: () => api<User[]>("/api/users"),
  // Search users by email or display name
  search: (query: string) => api<User[]>(`/api/users/search?query=${encodeURIComponent(query)}`),
};

export const TasksAPI = {
  // Get all tasks for a project, optionally including archived ones
  list: (projectId: string, includeArchived: boolean = false) => 
    api<Task[]>(`/api/projects/${projectId}/tasks${includeArchived ? '?include_archived=true' : ''}`),
  // Get a specific task by ID
  getById: (taskId: string) => api<Task>(`/api/tasks/${taskId}`),
  // Create a new task in a project
  create: (projectId: string, taskData: {
    title: string;
    description?: string;
    due_date?: string;
    notes?: string;
    assignee_ids?: string[];
    status?: "todo" | "in_progress" | "completed" | "blocked";
    tags?: string; // Free text with # separator
    priority?: number; // Priority 1-10
  }) =>
    api<Task>(`/api/projects/${projectId}/tasks`, {
      method: "POST",
      body: JSON.stringify(taskData),
    }),
  // Update an existing task
  update: (taskId: string, updates: Partial<Task>) =>
    api<Task>(`/api/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(updates),
    }),
  // Update task assignees
  updateAssignees: (taskId: string, assignee_ids: string[]) =>
    api<Task>(`/api/tasks/${taskId}/assignees`, {
      method: "PATCH",
      body: JSON.stringify({ assignee_ids }),
    }),
  // Delete a task permanently
  delete: (taskId: string) =>
    api(`/api/tasks/${taskId}`, {
      method: "DELETE",
    }),
  // Archive a task (soft delete)
  archive: (taskId: string) =>
    api<Task>(`/api/tasks/${taskId}/archive`, {
      method: "PATCH",
    }),
  // Restore an archived task
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
  // Get all comments for a task
  list: (taskId: string) => api<Comment[]>(`/api/tasks/${taskId}/comments`),
  // Create a new comment or reply to a comment
  create: (taskId: string, content: string, parentCommentId?: string) =>
    api<Comment>(`/api/tasks/${taskId}/comments`, {
      method: "POST",
      body: JSON.stringify({ 
        content, 
        task_id: taskId, 
        parent_comment_id: parentCommentId 
      }),
    }),
  // Update an existing comment
  update: (commentId: string, content: string) =>
    api<Comment>(`/api/comments/${commentId}`, {
      method: "PUT",
      body: JSON.stringify({ content }),
    }),
  // Delete a comment
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
  // Get all subtasks for a task
  list: (taskId: string) => api<SubTask[]>(`/api/tasks/${taskId}/subtasks`),
  // Get a specific subtask by ID
  getById: (subtaskId: string) => api<SubTask>(`/api/tasks/subtasks/${subtaskId}`),
  // Create a new subtask for a task
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
  // Update an existing subtask
  update: (subtaskId: string, updates: Partial<SubTask>) =>
    api<SubTask>(`/api/tasks/subtasks/${subtaskId}`, {
      method: "PATCH",
      body: JSON.stringify(updates),
    }),
  // Delete a subtask permanently
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
  task_id?: string;
  subtask_id?: string;
  uploaded_by: string;
  created_at: string;
  download_url?: string;
  uploader_email?: string;
  uploader_display_name?: string;
};

export const FilesAPI = {
  // Get all files attached to a task
  list: (taskId: string) => api<TaskFile[]>(`/api/tasks/${taskId}/files`),
  // Upload a file to a task
  upload: (taskId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api<TaskFile>(`/api/tasks/${taskId}/files`, {
      method: "POST",
      body: formData,
    });
  },
  // Get all files attached to a subtask
  listForSubtask: (subtaskId: string) => api<TaskFile[]>(`/api/tasks/subtasks/${subtaskId}/files`),
  // Upload a file to a subtask
  uploadForSubtask: (subtaskId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api<TaskFile>(`/api/tasks/subtasks/${subtaskId}/files`, {
      method: "POST",
      body: formData,
    });
  },
  // Delete a file from a task or subtask
  delete: (fileId: string) =>
    api(`/api/tasks/files/${fileId}`, {
      method: "DELETE",
    }),
};

// Team types and API
export type Team = {
  id: string;
  name: string;
  description?: string;
  manager_id: string;
  created_at: string;
  updated_at: string;
};

export type TeamMember = {
  id: string;
  team_id: string;
  user_id: string;
  role: "member" | "manager";
  joined_at: string;
};

export const TeamsAPI = {
  // Get teams that the current user is a member of
  list: () => api<Team[]>("/api/teams"),
  // Get all teams in the system (admin only)
  listAll: () => api<Team[]>("/api/teams/admin/all"),
  // Get a specific team by ID
  getById: (teamId: string) => api<Team>(`/api/teams/${teamId}`),
  // Create a new team
  create: (name: string, description?: string) =>
    api<Team>("/api/teams", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    }),
  // Update a team
  update: (teamId: string, updates: { name?: string; description?: string }) =>
    api<Team>(`/api/teams/${teamId}`, {
      method: "PUT",
      body: JSON.stringify(updates),
    }),
  // Delete a team
  delete: (teamId: string) =>
    api(`/api/teams/${teamId}`, {
      method: "DELETE",
    }),
  // Get team members
  getMembers: (teamId: string) => api<TeamMember[]>(`/api/teams/${teamId}/members`),
  // Add member to team
  addMember: (teamId: string, userId: string, role: "member" | "manager" = "member") =>
    api(`/api/teams/${teamId}/members`, {
      method: "POST",
      body: JSON.stringify({ member_user_id: userId, role }),
    }),
  // Remove member from team
  removeMember: (teamId: string, userId: string) =>
    api(`/api/teams/${teamId}/members/${userId}`, {
      method: "DELETE",
    }),
};

// Notification types and API
export type Notification = {
  id: string;
  user_id: string;
  type: "task_update" | "mention" | "task_assigned" | "deadline_reminder" | "overdue" | "daily_digest";
  title: string;
  message: string;
  read: boolean;
  created_at: string;
  link_url?: string | null;
  metadata?: Record<string, any>;
};

export const NotificationsAPI = {
  // Get notifications for current user
  list: (limit: number = 20, offset: number = 0, includeRead: boolean = true) =>
    api<Notification[]>(`/api/notifications?limit=${limit}&offset=${offset}&include_read=${includeRead}`),
  // Get unread count
  getUnreadCount: () => api<{ count: number }>("/api/notifications/unread-count"),
  // Mark notification as read
  markAsRead: (notificationId: string) =>
    api<{ message: string }>(`/api/notifications/${notificationId}/read`, {
      method: "PATCH",
    }),
  // Mark all notifications as read
  markAllAsRead: () =>
    api<{ message: string }>("/api/notifications/mark-all-read", {
      method: "PATCH",
    }),
};

// Account lockout types and API
export type LockedAccount = {
  email: string;
  locked_until: string;
  locked_at: string;
  lockout_reason?: string;
};

export const AuthAPI = {
  // Get list of all locked accounts (admin only)
  listLockedAccounts: () => {
    return api<{ success: boolean; data: { accounts: LockedAccount[] } }>("/api/auth/locked-accounts");
  },
  // Unlock an account by email (admin only)
  unlockAccount: (email: string) =>
    api<{ success: boolean; message: string }>("/api/auth/unlock-account", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
};

