"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import {
  ProjectsAPI,
  TasksAPI,
  CommentsAPI,
  SubTasksAPI,
  FilesAPI,
  Project,
  Task,
  User,
  Comment,
  SubTask,
  TaskFile,
} from "@/lib/api";
import { isAdmin, isManager, canAdminManage } from "@/utils/role-utils";
import CreateSubTaskModal from "@/components/CreateSubTaskModal";
import {
  ArrowLeft,
  Edit,
  Trash2,
  MessageSquare,
  CheckSquare,
  Check,
  Paperclip,
  Plus,
  Calendar,
  User as UserIcon,
  Clock,
  AlertCircle,
  Save,
  X,
  Flag,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import AssigneeSelector from "@/components/AssigneeSelector";

// Helper function to format date in Singapore time
const formatSingaporeTime = (dateString: string): string => {
  try {
    // Normalize timestamp: ensure it has timezone info
    let normalizedDateString = dateString;
    
    // If timestamp doesn't have timezone info, assume it's UTC and append 'Z'
    if (dateString && !dateString.endsWith('Z') && !dateString.includes('+') && !dateString.includes('-', 10)) {
      // Check if it's a valid ISO format without timezone (e.g., "2023-10-27T12:57:00")
      if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$/.test(dateString)) {
        normalizedDateString = dateString + 'Z';
      }
    }
    
    // Parse the date - JavaScript's Date will interpret 'Z' as UTC
    const date = new Date(normalizedDateString);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      console.warn("Invalid date string:", dateString);
      return dateString; // Return original if invalid
    }
    
    // Format in Singapore timezone
    return date.toLocaleString("en-SG", {
      timeZone: "Asia/Singapore",
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false, // Use 24-hour format
    });
  } catch (error) {
    console.error("Error formatting date:", error, dateString);
    return dateString;
  }
};

// Recursive Comment Component
function CommentItem({
  comment,
  user,
  onReply,
  onDelete,
  onEdit,
  isAdmin,
  isManager,
  projectMembers,
  insertMention,
  mentionSuggestions,
  showMentionSuggestions,
  setShowMentionSuggestions,
  setMentionQuery,
  selectedMentionIndex,
  setSelectedMentionIndex,
}: {
  comment: Comment;
  user: any;
  onReply: (parentId: string, replyText: string) => void;
  onDelete: (commentId: string) => void;
  onEdit: (commentId: string, content: string) => void;
  isAdmin: (user: any) => boolean;
  isManager: (user: any) => boolean;
  projectMembers: User[];
  insertMention: (member: User, targetTextarea?: HTMLTextAreaElement) => void;
  mentionSuggestions: User[];
  showMentionSuggestions: boolean;
  setShowMentionSuggestions: (show: boolean) => void;
  setMentionQuery: (query: string) => void;
  selectedMentionIndex: number;
  setSelectedMentionIndex: (index: number) => void;
}) {
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(comment.content);
  const [showReplyMentions, setShowReplyMentions] = useState(false);
  const [replyMentionQuery, setReplyMentionQuery] = useState("");
  const [selectedReplyMentionIndex, setSelectedReplyMentionIndex] = useState(0);
  const isCreator = user?.id === comment.user_id;
  const canDelete = isCreator || isAdmin(user);
  const canEdit = isCreator;
  
  // Filter mentionable users for replies
  const replyMentionSuggestions = projectMembers.filter((member) => {
    if (!replyMentionQuery) return true;
    const query = replyMentionQuery.toLowerCase();
    const displayName = (member.display_name || "").toLowerCase();
    const email = (member.email || "").toLowerCase();
    return displayName.includes(query) || email.includes(query);
  }).slice(0, 5);
  
  // Insert mention into reply
  const insertReplyMention = (member: User, textarea: HTMLTextAreaElement) => {
    const cursorPos = textarea.selectionStart;
    const textBeforeCursor = replyText.substring(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf("@");
    
    if (lastAtIndex !== -1) {
      const mentionName = member.display_name || member.email?.split("@")[0] || "Unknown";
      const newText = 
        replyText.substring(0, lastAtIndex) + 
        `@${mentionName} ` + 
        replyText.substring(cursorPos);
      setReplyText(newText);
      setShowReplyMentions(false);
      setReplyMentionQuery("");
      setSelectedReplyMentionIndex(0);
      
      setTimeout(() => {
        const newCursorPos = lastAtIndex + mentionName.length + 2;
        textarea.setSelectionRange(newCursorPos, newCursorPos);
        textarea.focus();
      }, 0);
    }
  };

  // Update editText when comment content changes
  useEffect(() => {
    if (!isEditing) {
      setEditText(comment.content);
    }
  }, [comment.content, isEditing]);

  const handleReply = () => {
    if (replyText.trim()) {
      onReply(comment.id, replyText);
      setReplyText("");
      setShowReplyForm(false);
    }
  };

  const handleEdit = () => {
    if (editText.trim() && editText !== comment.content) {
      onEdit(comment.id, editText.trim());
      setIsEditing(false);
    } else {
      setIsEditing(false);
      setEditText(comment.content);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditText(comment.content);
  };

  return (
    <div className="space-y-3">
      <div className="flex gap-3">
        <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center text-white text-sm font-medium">
          {comment.user_display_name?.charAt(0) ||
            comment.user_email?.charAt(0) ||
            "U"}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-gray-900">
              {comment.user_display_name ||
                comment.user_email?.split("@")[0] ||
                "Unknown"}
            </span>
            <span className="text-xs text-gray-500">
              {formatSingaporeTime(comment.created_at)}
            </span>
            <div className="flex items-center gap-2 ml-auto">
              {canEdit && !isEditing && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="text-blue-500 hover:text-blue-700 text-xs"
                  title="Edit comment"
                >
                  <Edit className="h-3 w-3" />
                </button>
              )}
              {canDelete && (
                <button
                  onClick={() => onDelete(comment.id)}
                  className="text-red-500 hover:text-red-700 text-xs"
                  title={isCreator ? "Delete your comment" : "Delete comment (Admin)"}
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              )}
            </div>
          </div>
          {isEditing ? (
            <div className="mb-2">
              <textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md resize-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
                rows={3}
                autoFocus
              />
              <div className="flex gap-2 mt-2">
                <button
                  onClick={handleEdit}
                  disabled={!editText.trim() || editText === comment.content}
                  className="px-3 py-1 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Save
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="px-3 py-1 bg-gray-500 text-white text-xs rounded-md hover:bg-gray-600"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-700 whitespace-pre-wrap mb-2">
              {comment.content.split(/(@[\w\s]+?)(?=\s|$|[.,!?;:])/).map((part, index) => {
                if (part.startsWith("@")) {
                  return (
                    <span key={index} className="bg-blue-100 text-blue-700 px-1 rounded font-medium">
                      {part}
                    </span>
                  );
                }
                return <span key={index}>{part}</span>;
              })}
            </p>
          )}
          {!isEditing && (
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowReplyForm(!showReplyForm)}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Reply
              </button>
            </div>
          )}

          {/* Reply Form */}
          {showReplyForm && (
            <div className="mt-3 ml-4 border-l-2 border-gray-200 pl-4">
              <div className="flex gap-2">
                <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-medium">
                  {user?.email?.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 relative">
                  <textarea
                    value={replyText}
                    onChange={(e) => {
                      setReplyText(e.target.value);
                      // Check for @ mentions in reply
                      const text = e.target.value;
                      const cursorPos = e.target.selectionStart;
                      const textBeforeCursor = text.substring(0, cursorPos);
                      const lastAtIndex = textBeforeCursor.lastIndexOf("@");
                      
                      if (lastAtIndex !== -1) {
                        const textAfterAt = textBeforeCursor.substring(lastAtIndex + 1);
                        if (/^\w*$/.test(textAfterAt)) {
                          setShowReplyMentions(true);
                          setReplyMentionQuery(textAfterAt);
                        } else {
                          setShowReplyMentions(false);
                        }
                      } else {
                        setShowReplyMentions(false);
                      }
                    }}
                    onKeyDown={(e) => {
                      if (showReplyMentions && replyMentionSuggestions.length > 0) {
                        if (e.key === "ArrowDown") {
                          e.preventDefault();
                          setSelectedReplyMentionIndex((prev) => 
                            prev < replyMentionSuggestions.length - 1 ? prev + 1 : prev
                          );
                        } else if (e.key === "ArrowUp") {
                          e.preventDefault();
                          setSelectedReplyMentionIndex((prev) => (prev > 0 ? prev - 1 : 0));
                        } else if (e.key === "Enter" && selectedReplyMentionIndex >= 0) {
                          e.preventDefault();
                          insertReplyMention(replyMentionSuggestions[selectedReplyMentionIndex], e.currentTarget);
                        } else if (e.key === "Escape") {
                          setShowReplyMentions(false);
                        }
                      }
                    }}
                    placeholder="Write a reply... Use @ to mention someone"
                    className="w-full p-2 border border-gray-300 rounded-md resize-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    rows={2}
                  />
                  {/* Mention Suggestions for Reply */}
                  {showReplyMentions && replyMentionSuggestions.length > 0 && (
                    <div className="absolute bottom-full left-0 right-0 mb-1 bg-white border border-gray-300 rounded-md shadow-lg z-20 max-h-48 overflow-y-auto">
                      {replyMentionSuggestions.map((member, index) => (
                        <button
                          key={member.id}
                          type="button"
                          onClick={() => {
                            const textarea = document.querySelector('textarea[placeholder*="Write a reply"]') as HTMLTextAreaElement;
                            if (textarea) {
                              insertReplyMention(member, textarea);
                            }
                          }}
                          className={`w-full px-3 py-2 text-left hover:bg-blue-50 flex items-center gap-2 text-sm ${
                            index === selectedReplyMentionIndex ? "bg-blue-50" : ""
                          }`}
                        >
                          <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-medium">
                            {(member.display_name || member.email || "U").charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div className="font-medium">
                              {member.display_name || member.email?.split("@")[0] || "Unknown"}
                            </div>
                            {member.email && (
                              <div className="text-xs text-gray-500">{member.email}</div>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={handleReply}
                      disabled={!replyText.trim()}
                      className="px-3 py-1 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Reply
                    </button>
                    <button
                      onClick={() => {
                        setShowReplyForm(false);
                        setReplyText("");
                        setShowReplyMentions(false);
                      }}
                      className="px-3 py-1 bg-gray-500 text-white text-xs rounded-md hover:bg-gray-600"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Render Replies */}
      {comment.replies && comment.replies.length > 0 && (
        <div className="ml-8 space-y-3">
          {comment.replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              user={user}
              onReply={onReply}
              onDelete={onDelete}
              onEdit={onEdit}
              isAdmin={isAdmin}
              isManager={isManager}
              projectMembers={projectMembers}
              insertMention={insertMention}
              mentionSuggestions={mentionSuggestions}
              showMentionSuggestions={showMentionSuggestions}
              setShowMentionSuggestions={setShowMentionSuggestions}
              setMentionQuery={setMentionQuery}
              selectedMentionIndex={selectedMentionIndex}
              setSelectedMentionIndex={setSelectedMentionIndex}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function TaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const projectId = params.id as string;
  const taskId = params.taskId as string;

  const [project, setProject] = useState<Project | null>(null);
  const [task, setTask] = useState<Task | null>(null);
  const [projectMembers, setProjectMembers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  // Comments, sub-tasks, and files state
  const [comments, setComments] = useState<Comment[]>([]);
  const [subtasks, setSubtasks] = useState<SubTask[]>([]);
  const [files, setFiles] = useState<TaskFile[]>([]);
  const [newComment, setNewComment] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [deleteConfirmDialog, setDeleteConfirmDialog] = useState<{
    isOpen: boolean;
    file: TaskFile | null;
  }>({
    isOpen: false,
    file: null,
  });
  const [errorDialog, setErrorDialog] = useState<{
    isOpen: boolean;
    message: string;
  }>({
    isOpen: false,
    message: "",
  });
  
  // Mention state
  const [showMentionSuggestions, setShowMentionSuggestions] = useState(false);
  const [mentionQuery, setMentionQuery] = useState("");
  const [selectedMentionIndex, setSelectedMentionIndex] = useState(0);
  
  // Filter mentionable users based on query
  const mentionSuggestions = projectMembers.filter((member) => {
    if (!mentionQuery) return true;
    const query = mentionQuery.toLowerCase();
    const displayName = (member.display_name || "").toLowerCase();
    const email = (member.email || "").toLowerCase();
    return displayName.includes(query) || email.includes(query);
  }).slice(0, 5); // Limit to 5 suggestions
  
  // Insert mention into comment (works for both main comment and replies)
  const insertMention = (member: User, targetTextarea?: HTMLTextAreaElement) => {
    const textarea = targetTextarea || (document.querySelector('textarea[placeholder*="mention"]') as HTMLTextAreaElement);
    if (!textarea) return;
    
    const isReply = textarea !== document.querySelector('textarea[placeholder*="Add a comment"]');
    const currentText = isReply ? replyText : newComment;
    const setText = isReply ? setReplyText : setNewComment;
    
    const cursorPos = textarea.selectionStart;
    const textBeforeCursor = currentText.substring(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf("@");
    
    if (lastAtIndex !== -1) {
      const mentionName = member.display_name || member.email?.split("@")[0] || "Unknown";
      const newText = 
        currentText.substring(0, lastAtIndex) + 
        `@${mentionName} ` + 
        currentText.substring(cursorPos);
      setText(newText);
      setShowMentionSuggestions(false);
      setMentionQuery("");
      setSelectedMentionIndex(0);
      
      // Set cursor position after the mention
      setTimeout(() => {
        const newCursorPos = lastAtIndex + mentionName.length + 2; // +2 for @ and space
        textarea.setSelectionRange(newCursorPos, newCursorPos);
        textarea.focus();
      }, 0);
    }
  };

  // Sub-comment state
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyText, setReplyText] = useState("");

  // Sub-task modal state
  const [showSubTaskModal, setShowSubTaskModal] = useState(false);
  const [creatingSubTask, setCreatingSubTask] = useState(false);

  // Confirmation dialog state
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean;
    title: string;
    description: string;
    onConfirm: () => void;
    variant?: "default" | "destructive";
  }>({
    isOpen: false,
    title: "",
    description: "",
    onConfirm: () => {},
    variant: "default",
  });

  // Edit form state
  const [editForm, setEditForm] = useState({
    title: "",
    description: "",
    status: "todo" as Task["status"],
    notes: "",
    assignee_ids: [] as string[],
    priority: undefined as number | undefined,
    due_date: "" as string,
  });

  // Load project and task details
  const loadData = async () => {
    try {
      setLoading(true);

      // Try to get project directly by ID first (works for admins and members)
      let foundProject;
      try {
        foundProject = await ProjectsAPI.getById(projectId);
      } catch (err) {
        // If direct access fails, try loading from user's projects
        console.log("Direct project access failed, trying user projects");
        const projects = await ProjectsAPI.list();
        foundProject = projects.find((p) => p.id === projectId);
      }

      if (!foundProject) {
        setError("Project not found");
        return;
      }

      const [
        taskData,
        projectMembersData,
        commentsData,
        subtasksData,
        filesData,
      ] = await Promise.all([
        TasksAPI.getById(taskId),
        ProjectsAPI.getMembers(projectId), // Get project members directly
        CommentsAPI.list(taskId).catch((err) => {
          console.error("Error loading comments:", err);
          return [];
        }),
        SubTasksAPI.list(taskId).catch((err) => {
          console.error("Error loading subtasks:", err);
          return [];
        }),
        FilesAPI.list(taskId).catch((err) => {
          console.error("Error loading files:", err);
          return [];
        }),
      ]);

      setProject(foundProject);

      // Convert project members data to User format for AssigneeSelector
      const members: User[] = projectMembersData.map((member: any) => ({
        id: member.user_id,
        email: member.user_email,
        display_name: member.user_display_name,
        roles: [member.role], // Convert role to roles array
      }));

      setProjectMembers(members);

      if (taskData) {
        setTask(taskData);
        // Convert backend date format to datetime-local format (YYYY-MM-DDTHH:mm)
        let formattedDueDate = "";
        if (taskData.due_date) {
          const date = new Date(taskData.due_date);
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const day = String(date.getDate()).padStart(2, '0');
          const hours = String(date.getHours()).padStart(2, '0');
          const minutes = String(date.getMinutes()).padStart(2, '0');
          formattedDueDate = `${year}-${month}-${day}T${hours}:${minutes}`;
        }
        // Initialize edit form with current task data
        setEditForm({
          title: taskData.title,
          description: taskData.description || "",
          status: taskData.status,
          notes: taskData.notes || "",
          assignee_ids: taskData.assignee_ids || [],
          priority: taskData.priority,
          due_date: formattedDueDate,
        });
      } else {
        setError("Task not found");
        return;
      }

      // Set comments, sub-tasks, and files
      console.log("Comments data:", commentsData);
      console.log("Comments data type:", typeof commentsData);
      console.log("Comments data length:", commentsData?.length);
      setComments(commentsData);
      setSubtasks(subtasksData);
      setFiles(filesData);
    } catch (err: any) {
      setError("Failed to load task details");
    } finally {
      setLoading(false);
    }
  };

  // Get status color
  const getStatusColor = (status: Task["status"]) => {
    switch (status) {
      case "todo":
        return "bg-gray-100 text-gray-800";
      case "in_progress":
        return "bg-blue-100 text-blue-800";
      case "completed":
        return "bg-green-100 text-green-800";
      case "blocked":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  // Get status icon
  const getStatusIcon = (status: Task["status"]) => {
    switch (status) {
      case "todo":
        return <CheckSquare className="h-4 w-4" />;
      case "in_progress":
        return <Clock className="h-4 w-4" />;
      case "completed":
        return <CheckSquare className="h-4 w-4" />;
      case "blocked":
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <CheckSquare className="h-4 w-4" />;
    }
  };

  // Check if user can edit this task
  const canEditTask = () => {
    if (!task || !user) return false;

    // Admin+Manager/Staff can edit, but admin alone is read-only
    if (canAdminManage(user)) return true;

    // Managers can always edit
    if (isManager(user)) return true;

    // Project owners can edit
    if (project?.owner_id === user.id) return true;

    // Task assignees can edit
    return task.assignee_ids?.includes(user.id) || false;
  };

  // Check if user can archive this task
  const canArchiveTask = () => {
    if (!task || !user) return false;

    // Admin+Manager/Staff can archive, but admin alone is read-only
    if (canAdminManage(user)) return true;

    // Managers can archive
    if (isManager(user)) return true;

    // Project owners can archive
    if (project?.owner_id === user.id) return true;

    return false;
  };

  // Save task updates
  const saveTask = async () => {
    if (!task) return;

    // Validate that at least one assignee is selected
    if (!editForm.assignee_ids || editForm.assignee_ids.length === 0) {
      setError("At least one assignee is required");
      return;
    }

    try {
      setSaving(true);
      setError("");

      // Convert datetime-local format to backend format (YYYY-MM-DD HH:MM:SS)
      let formattedDueDate = undefined;
      if (editForm.due_date) {
        const date = new Date(editForm.due_date);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        formattedDueDate = `${year}-${month}-${day} ${hours}:${minutes}:00`;
      }

      // Update task via API
      const updatedTask = await TasksAPI.update(task.id, {
        title: editForm.title,
        description: editForm.description,
        status: editForm.status,
        notes: editForm.notes,
        assignee_ids: editForm.assignee_ids,
        priority: editForm.priority,
        due_date: formattedDueDate,
      });

      // Update local state
      setTask(updatedTask);
      setEditing(false);
    } catch (err: any) {
      setError(err.message || "Failed to update task");
    } finally {
      setSaving(false);
    }
  };

  // Cancel editing
  const cancelEdit = () => {
    if (task) {
      // Convert backend date format to datetime-local format (YYYY-MM-DDTHH:mm)
      let formattedDueDate = "";
      if (task.due_date) {
        const date = new Date(task.due_date);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        formattedDueDate = `${year}-${month}-${day}T${hours}:${minutes}`;
      }
      setEditForm({
        title: task.title,
        description: task.description || "",
        status: task.status,
        notes: task.notes || "",
        assignee_ids: task.assignee_ids || [],
        priority: task.priority,
        due_date: formattedDueDate,
      });
    }
    setEditing(false);
  };

  // Archive task
  const archiveTask = async () => {
    if (!task) return;

    try {
      await TasksAPI.archive(task.id);
      router.push(`/projects/${projectId}`);
    } catch (err: any) {
      setError("Failed to archive task");
    }
  };

  // Add comment
  const addComment = async () => {
    if (!newComment.trim() || !task) return;

    try {
      const comment = await CommentsAPI.create(task.id, newComment.trim());
      // Ensure comment has proper structure with empty replies array
      const newCommentWithReplies: Comment = {
        ...comment,
        replies: comment.replies || [],
        user_display_name: comment.user_display_name || user?.display_name,
        user_email: comment.user_email || user?.email,
      };
      setComments([...comments, newCommentWithReplies]);
      setNewComment("");
    } catch (err: any) {
      setError("Failed to add comment");
    }
  };

  // Add reply to comment
  const addReply = async (parentCommentId: string, replyText: string) => {
    if (!replyText.trim() || !task) return;

    try {
      const reply = await CommentsAPI.create(
        task.id,
        replyText.trim(),
        parentCommentId
      );
      
      // Ensure reply has proper structure
      const newReply: Comment = {
        ...reply,
        replies: [],
        user_display_name: reply.user_display_name || user?.display_name,
        user_email: reply.user_email || user?.email,
      };
      
      // Immediately add reply to parent comment's replies array
      setComments(comments.map(comment => {
        if (comment.id === parentCommentId) {
          return {
            ...comment,
            replies: [...(comment.replies || []), newReply],
          };
        }
        // Also check nested replies
        if (comment.replies) {
          return {
            ...comment,
            replies: comment.replies.map(replyItem => {
              if (replyItem.id === parentCommentId) {
                return {
                  ...replyItem,
                  replies: [...(replyItem.replies || []), newReply],
                };
              }
              return replyItem;
            }),
          };
        }
        return comment;
      }));
    } catch (err: any) {
      console.error("Error adding reply:", err);
      setError("Failed to add reply");
    }
  };

  // Delete comment (creator or admin only)
  const deleteComment = async (commentId: string) => {
    const comment = comments.find((c) => c.id === commentId) || 
                    comments.flatMap(c => c.replies || []).find((r) => r.id === commentId);
    
    if (!comment) {
      setError("Comment not found");
      return;
    }

    const isCreator = user?.id === comment.user_id;
    if (!isCreator && !isAdmin(user)) {
      setError("Only the comment creator or admin can delete comments");
      return;
    }

    try {
      await CommentsAPI.delete(commentId);
      // Remove comment from list (including nested replies)
      const removeComment = (commentList: Comment[]): Comment[] => {
        return commentList
          .filter((c) => c.id !== commentId)
          .map((c) => ({
            ...c,
            replies: c.replies ? removeComment(c.replies) : undefined,
          }));
      };
      setComments(removeComment(comments));
    } catch (err: any) {
      setError("Failed to delete comment");
    }
  };

  // Edit comment (creator only)
  const editComment = async (commentId: string, content: string) => {
    const comment = comments.find((c) => c.id === commentId) || 
                    comments.flatMap(c => c.replies || []).find((r) => r.id === commentId);
    
    if (!comment) {
      setError("Comment not found");
      return;
    }

    if (user?.id !== comment.user_id) {
      setError("Only the comment creator can edit comments");
      return;
    }

    try {
      const updatedComment = await CommentsAPI.update(commentId, content);
      // Update comment in list (including nested replies)
      const updateComment = (commentList: Comment[]): Comment[] => {
        return commentList.map((c) => {
          if (c.id === commentId) {
            return { ...updatedComment, replies: c.replies };
          }
          return {
            ...c,
            replies: c.replies ? updateComment(c.replies) : undefined,
          };
        });
      };
      setComments(updateComment(comments));
    } catch (err: any) {
      setError("Failed to update comment");
    }
  };

  // Add sub-task
  const addSubtask = async (subtaskData: {
    title: string;
    description: string;
    status: "todo" | "in_progress" | "completed" | "blocked";
    due_date?: string;
    assignee_ids: string[];
    tags: string[];
    notes: string;
  }) => {
    if (!task) return;

    try {
      setCreatingSubTask(true);
      const subtask = await SubTasksAPI.create(task.id, {
        title: subtaskData.title.trim(),
        description: subtaskData.description.trim() || undefined,
        status: subtaskData.status,
        due_date: subtaskData.due_date,
        assignee_ids: subtaskData.assignee_ids,
        tags: subtaskData.tags,
        notes: subtaskData.notes.trim() || undefined,
      });
      setSubtasks([...subtasks, subtask]);
    } catch (err: any) {
      setError("Failed to add sub-task");
    } finally {
      setCreatingSubTask(false);
    }
  };

  // Upload file
  const uploadFile = async () => {
    if (!selectedFile || !task) return;

    try {
      setUploadingFile(true);
      const file = await FilesAPI.upload(task.id, selectedFile);
      setFiles([...files, file]);
      setSelectedFile(null);
    } catch (err: any) {
      setError("Failed to upload file");
    } finally {
      setUploadingFile(false);
    }
  };

  // Download file
  const downloadFile = async (file: TaskFile) => {
    try {
      const response = await fetch(`/api/tasks/files/${file.id}/download`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.original_filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Error downloading file:", error);
      setError("Failed to download file");
    }
  };

  // Delete file
  const handleDeleteClick = (file: TaskFile) => {
    setDeleteConfirmDialog({ isOpen: true, file });
  };

  const handleDeleteConfirm = async () => {
    if (!deleteConfirmDialog.file) return;
    
    try {
      await FilesAPI.delete(deleteConfirmDialog.file.id);
      // Refresh files list
      const updatedFiles = await FilesAPI.list(taskId);
      setFiles(updatedFiles);
      setDeleteConfirmDialog({ isOpen: false, file: null });
    } catch (error) {
      console.error("Error deleting file:", error);
      setDeleteConfirmDialog({ isOpen: false, file: null });
      setErrorDialog({
        isOpen: true,
        message: "Failed to delete file. You may only delete files you uploaded.",
      });
    }
  };

  // Update sub-task status
  const updateSubtaskStatus = async (
    subtaskId: string,
    status: SubTask["status"]
  ) => {
    try {
      const updatedSubtask = await SubTasksAPI.update(subtaskId, { status });
      setSubtasks(
        subtasks.map((st) => (st.id === subtaskId ? updatedSubtask : st))
      );
    } catch (err: any) {
      setError("Failed to update sub-task");
    }
  };

  // Delete sub-task
  const deleteSubtask = async (subtaskId: string) => {
    try {
      await SubTasksAPI.delete(subtaskId);
      setSubtasks(subtasks.filter((st) => st.id !== subtaskId));
    } catch (err: any) {
      setError("Failed to delete sub-task");
    }
  };

  useEffect(() => {
    if (projectId && taskId) {
      loadData();
    }
  }, [projectId, taskId]);

  if (loading) {
    return <TaskDetailSkeleton />;
  }

  if (error || !project || !task) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || "Task not found"}</p>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{task.title}</h1>
            <p className="text-gray-600">
              in <span className="font-medium">{project.name}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {canEditTask() && (
            <>
              {editing ? (
                <>
                  <button
                    onClick={saveTask}
                    disabled={saving}
                    className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                  >
                    <Save className="h-4 w-4" />
                    {saving ? "Saving..." : "Save"}
                  </button>
                  <button
                    onClick={cancelEdit}
                    className="flex items-center gap-2 px-3 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm"
                  >
                    <X className="h-4 w-4" />
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setEditing(true)}
                  className="p-2 hover:bg-gray-100 rounded-md transition-colors"
                  title="Edit task"
                >
                  <Edit className="h-5 w-5" />
                </button>
              )}
            </>
          )}
          {canArchiveTask() && (
            <button
              onClick={() => {
                setConfirmDialog({
                  isOpen: true,
                  title: "Archive Task",
                  description: `Are you sure you want to archive "${task?.title || "this task"}"?`,
                  variant: "default",
                  onConfirm: () => archiveTask(),
                });
              }}
              className="p-2 hover:bg-orange-100 rounded-md transition-colors text-orange-600"
              title="Archive task"
            >
              <Trash2 className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>

      {/* Task Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Description
            </h2>
            {editing ? (
              <textarea
                value={editForm.description}
                onChange={(e) =>
                  setEditForm({ ...editForm, description: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 resize-none"
                rows={4}
                placeholder="Add a description..."
              />
            ) : task.description ? (
              <p className="text-gray-700 whitespace-pre-wrap">
                {task.description}
              </p>
            ) : (
              <p className="text-gray-500 italic">No description provided</p>
            )}
          </div>

          {/* Comments */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-4">
              <MessageSquare className="h-5 w-5" />
              <h2 className="text-lg font-semibold text-gray-900">
                Comments ({comments.length})
              </h2>
            </div>
            <div className="space-y-4">
              {/* Comment Input */}
              {canEditTask() && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                    {user?.email?.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 relative">
                    <textarea
                      value={newComment}
                      onChange={(e) => {
                        setNewComment(e.target.value);
                        // Check for @ mentions
                        const text = e.target.value;
                        const cursorPos = e.target.selectionStart;
                        const textBeforeCursor = text.substring(0, cursorPos);
                        const lastAtIndex = textBeforeCursor.lastIndexOf("@");
                        
                        if (lastAtIndex !== -1) {
                          const textAfterAt = textBeforeCursor.substring(lastAtIndex + 1);
                          // If @ is followed by word characters, show mention suggestions
                          if (/^\w*$/.test(textAfterAt)) {
                            setShowMentionSuggestions(true);
                            setMentionQuery(textAfterAt);
                          } else {
                            setShowMentionSuggestions(false);
                          }
                        } else {
                          setShowMentionSuggestions(false);
                        }
                      }}
                      onKeyDown={(e) => {
                        if (showMentionSuggestions && mentionSuggestions.length > 0) {
                          if (e.key === "ArrowDown") {
                            e.preventDefault();
                            setSelectedMentionIndex((prev) => 
                              prev < mentionSuggestions.length - 1 ? prev + 1 : prev
                            );
                          } else if (e.key === "ArrowUp") {
                            e.preventDefault();
                            setSelectedMentionIndex((prev) => (prev > 0 ? prev - 1 : 0));
                          } else if (e.key === "Enter" && selectedMentionIndex >= 0) {
                            e.preventDefault();
                            insertMention(mentionSuggestions[selectedMentionIndex]);
                          } else if (e.key === "Escape") {
                            setShowMentionSuggestions(false);
                          }
                        }
                      }}
                      placeholder="Add a comment... Use @ to mention someone"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 resize-none"
                      rows={3}
                    />
                    {/* Mention Suggestions */}
                    {showMentionSuggestions && mentionSuggestions.length > 0 && (
                      <div className="absolute bottom-full left-0 right-0 mb-1 bg-white border border-gray-300 rounded-md shadow-lg z-20 max-h-48 overflow-y-auto">
                        {mentionSuggestions.map((member, index) => (
                          <button
                            key={member.id}
                            type="button"
                            onClick={() => insertMention(member)}
                            className={`w-full px-3 py-2 text-left hover:bg-blue-50 flex items-center gap-2 text-sm ${
                              index === selectedMentionIndex ? "bg-blue-50" : ""
                            }`}
                          >
                            <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-medium">
                              {(member.display_name || member.email || "U").charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <div className="font-medium">
                                {member.display_name || member.email?.split("@")[0] || "Unknown"}
                              </div>
                              {member.email && (
                                <div className="text-xs text-gray-500">{member.email}</div>
                              )}
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                    <div className="flex items-center justify-between mt-2">
                      <p className="text-xs text-gray-500">
                        Type @ to mention someone. They'll receive an email notification.
                      </p>
                      <button
                        onClick={addComment}
                        disabled={!newComment.trim()}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                      >
                        Comment
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Comments List */}
              {comments.length > 0 ? (
                <div className="space-y-4">
                  {comments
                    .filter((comment) => !comment.parent_comment_id) // Only show top-level comments
                    .map((comment) => (
                      <CommentItem
                        key={comment.id}
                        comment={comment}
                        user={user}
                        onReply={(parentId, replyText) =>
                          addReply(parentId, replyText)
                        }
                        onDelete={deleteComment}
                        onEdit={editComment}
                        isAdmin={isAdmin}
                        isManager={isManager}
                        projectMembers={projectMembers}
                        insertMention={insertMention}
                        mentionSuggestions={mentionSuggestions}
                        showMentionSuggestions={showMentionSuggestions}
                        setShowMentionSuggestions={setShowMentionSuggestions}
                        setMentionQuery={setMentionQuery}
                        selectedMentionIndex={selectedMentionIndex}
                        setSelectedMentionIndex={setSelectedMentionIndex}
                      />
                    ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <MessageSquare className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                  <p className="text-sm">No comments yet</p>
                  <p className="text-xs text-gray-400">
                    Be the first to comment on this task
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Sub-tasks */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-50 rounded-lg">
                  <CheckSquare className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    Sub-tasks
                  </h2>
                  {subtasks.length > 0 && (
                    <div className="flex items-center gap-2 mt-1">
                      <div className="flex items-center gap-1 text-xs text-gray-500">
                        <span className="font-medium text-gray-700">
                          {subtasks.filter((st) => st.status === "completed").length}
                        </span>
                        <span>of</span>
                        <span className="font-medium text-gray-700">
                          {subtasks.length}
                        </span>
                        <span>completed</span>
                      </div>
                      <div className="h-1.5 w-24 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-green-500 transition-all duration-300"
                          style={{
                            width: `${
                              (subtasks.filter((st) => st.status === "completed")
                                .length /
                                subtasks.length) *
                              100
                            }%`,
                          }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
              {canEditTask() && (
                <button
                  onClick={() => setShowSubTaskModal(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm hover:shadow-md text-sm font-medium"
                >
                  <Plus className="h-4 w-4" />
                  Add Sub-task
                </button>
              )}
            </div>

            {subtasks.length > 0 ? (
              <div className="space-y-3">
                {subtasks.map((subtask) => {
                  const getStatusConfig = (status: SubTask["status"]) => {
                    switch (status) {
                      case "completed":
                        return {
                          color: "bg-green-50 border-green-200",
                          icon: "✓",
                          iconColor: "text-green-600",
                          badgeColor: "bg-green-100 text-green-700",
                        };
                      case "in_progress":
                        return {
                          color: "bg-blue-50 border-blue-200",
                          icon: "⟳",
                          iconColor: "text-blue-600",
                          badgeColor: "bg-blue-100 text-blue-700",
                        };
                      case "blocked":
                        return {
                          color: "bg-red-50 border-red-200",
                          icon: "⚠",
                          iconColor: "text-red-600",
                          badgeColor: "bg-red-100 text-red-700",
                        };
                      default:
                        return {
                          color: "bg-gray-50 border-gray-200",
                          icon: "○",
                          iconColor: "text-gray-600",
                          badgeColor: "bg-gray-100 text-gray-700",
                        };
                    }
                  };
                  const statusConfig = getStatusConfig(subtask.status);

                  return (
                    <div
                      key={subtask.id}
                      className={`group relative flex items-start gap-4 p-4 border-2 rounded-lg transition-all duration-200 hover:shadow-md ${statusConfig.color}`}
                    >
                      {/* Status Checkbox/Icon */}
                      <div className="flex-shrink-0 pt-0.5">
                        <button
                          onClick={() => {
                            const newStatus: SubTask["status"] =
                              subtask.status === "completed"
                                ? "todo"
                                : "completed";
                            updateSubtaskStatus(subtask.id, newStatus);
                          }}
                          className={`w-6 h-6 rounded-md border-2 flex items-center justify-center transition-all ${
                            subtask.status === "completed"
                              ? "bg-green-500 border-green-500 text-white"
                              : "bg-white border-gray-300 hover:border-green-400"
                          }`}
                        >
                          {subtask.status === "completed" && (
                            <Check className="h-4 w-4" />
                          )}
                        </button>
                      </div>

                      {/* Content */}
                      <div
                        className="flex-1 min-w-0 cursor-pointer"
                        onClick={() =>
                          router.push(
                            `/projects/${projectId}/tasks/${taskId}/subtasks/${subtask.id}`
                          )
                        }
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <h4
                              className={`text-sm font-semibold mb-1 transition-colors ${
                                subtask.status === "completed"
                                  ? "line-through text-gray-500"
                                  : "text-gray-900 group-hover:text-blue-600"
                              }`}
                            >
                              {subtask.title}
                            </h4>
                            {subtask.description && (
                              <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                                {subtask.description}
                              </p>
                            )}
                            <div className="flex items-center gap-3 mt-2">
                              {/* Status Badge */}
                              <Select
                                value={subtask.status}
                                onValueChange={(value: SubTask["status"]) =>
                                  updateSubtaskStatus(subtask.id, value)
                                }
                                onClick={(e) => e.stopPropagation()}
                              >
                                <SelectTrigger className={`h-7 w-28 text-xs ${statusConfig.badgeColor} border-0`}>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="todo">To Do</SelectItem>
                                  <SelectItem value="in_progress">
                                    In Progress
                                  </SelectItem>
                                  <SelectItem value="completed">
                                    Completed
                                  </SelectItem>
                                  <SelectItem value="blocked">Blocked</SelectItem>
                                </SelectContent>
                              </Select>

                              {/* Assignees */}
                              {subtask.assignee_names &&
                                subtask.assignee_names.length > 0 && (
                                  <div className="flex items-center gap-1">
                                    <UserIcon className="h-3 w-3 text-gray-400" />
                                    <span className="text-xs text-gray-500">
                                      {subtask.assignee_names.length}{" "}
                                      {subtask.assignee_names.length === 1
                                        ? "assignee"
                                        : "assignees"}
                                    </span>
                                  </div>
                                )}

                              {/* Due Date */}
                              {subtask.due_date && (
                                <div className="flex items-center gap-1 text-xs text-gray-500">
                                  <Calendar className="h-3 w-3" />
                                  {new Date(subtask.due_date).toLocaleDateString(
                                    "en-US",
                                    {
                                      month: "short",
                                      day: "numeric",
                                    }
                                  )}
                                </div>
                              )}

                              {/* Priority */}
                              {subtask.priority && (
                                <div className="flex items-center gap-1 text-xs">
                                  <Flag className={`h-3 w-3 ${
                                    subtask.priority >= 8 ? "text-red-500" :
                                    subtask.priority >= 5 ? "text-orange-500" :
                                    "text-yellow-500"
                                  }`} />
                                  <span className="text-gray-500">
                                    P{subtask.priority}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                      {canEditTask() && (
                        <div className="flex-shrink-0 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteSubtask(subtask.id);
                            }}
                            className="p-1.5 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
                            title="Delete subtask"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckSquare className="h-8 w-8 text-gray-400" />
                </div>
                <p className="text-sm font-medium text-gray-700 mb-1">
                  No sub-tasks yet
                </p>
                <p className="text-xs text-gray-400">
                  Break down this task into smaller, manageable pieces
                </p>
                {canEditTask() && (
                  <button
                    onClick={() => setShowSubTaskModal(true)}
                    className="mt-4 px-4 py-2 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
                  >
                    Create your first sub-task
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Files */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Paperclip className="h-5 w-5" />
                <h2 className="text-lg font-semibold text-gray-900">Files</h2>
              </div>
              {canEditTask() && (
                <label className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm cursor-pointer">
                  <Plus className="h-4 w-4" />
                  Upload File
                  <input
                    type="file"
                    className="hidden"
                    onChange={(e) =>
                      setSelectedFile(e.target.files?.[0] || null)
                    }
                    accept="*/*"
                  />
                </label>
              )}
            </div>

            {files.length > 0 ? (
              <div className="space-y-3">
                {files.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                  >
                    <div className="flex items-center space-x-3">
                      <Paperclip className="h-5 w-5 text-gray-400" />
                      <div>
                        <p className="font-medium text-gray-900">
                          {file.original_filename}
                        </p>
                        <p className="text-sm text-gray-500">
                          {(file.file_size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => downloadFile(file)}
                        className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 text-sm"
                      >
                        Download
                      </button>
                      <button
                        onClick={() => handleDeleteClick(file)}
                        className="px-3 py-1 bg-red-500 text-white rounded-md hover:bg-red-600 text-sm flex items-center space-x-1"
                        title="Delete file"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Paperclip className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">No files uploaded yet</p>
                <p className="text-xs text-gray-400">Upload files up to 50MB</p>
              </div>
            )}

            {selectedFile && (
              <div className="mt-4 pt-4 border-t">
                <div className="flex items-center space-x-3">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    onClick={uploadFile}
                    disabled={uploadingFile}
                    className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50 text-sm"
                  >
                    {uploadingFile ? "Uploading..." : "Upload"}
                  </button>
                  <button
                    onClick={() => setSelectedFile(null)}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 text-sm"
                  >
                    Cancel
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Maximum file size: 50MB
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Status */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Status</h3>
            {editing ? (
              <Select
                value={editForm.status}
                onValueChange={(value: Task["status"]) =>
                  setEditForm({ ...editForm, status: value })
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todo">
                    <div className="flex items-center gap-2">
                      <CheckSquare className="h-4 w-4" />
                      To Do
                    </div>
                  </SelectItem>
                  <SelectItem value="in_progress">
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      In Progress
                    </div>
                  </SelectItem>
                  <SelectItem value="completed">
                    <div className="flex items-center gap-2">
                      <CheckSquare className="h-4 w-4" />
                      Completed
                    </div>
                  </SelectItem>
                  <SelectItem value="blocked">
                    <div className="flex items-center gap-2">
                      <AlertCircle className="h-4 w-4" />
                      Blocked
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            ) : (
              <span
                className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                  task.status
                )}`}
              >
                {getStatusIcon(task.status)}
                {task.status === "todo"
                  ? "To do"
                  : task.status === "in_progress"
                  ? "In progress"
                  : task.status === "completed"
                  ? "Completed"
                  : task.status === "blocked"
                  ? "Blocked"
                  : (task.status as string).charAt(0).toUpperCase() +
                    (task.status as string).slice(1).replace("_", " ")}
              </span>
            )}
          </div>

          {/* Assignees */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-sm font-medium text-gray-900 mb-3">
              Assignees
            </h3>
            {editing ? (
              <AssigneeSelector
                users={projectMembers}
                selectedUserIds={editForm.assignee_ids}
                onSelectionChange={(userIds) =>
                  setEditForm({ ...editForm, assignee_ids: userIds })
                }
                maxAssignees={5}
                placeholder="Select assignees..."
              />
            ) : (
              <>
                {task.assignee_names && task.assignee_names.length > 0 ? (
                  <div className="space-y-2">
                    {task.assignee_names.map((name, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-xs font-medium">
                          {name.charAt(0).toUpperCase()}
                        </div>
                        <span className="text-sm text-gray-700">{name}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No assignees</p>
                )}
              </>
            )}
          </div>

          {/* Due Date */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-sm font-medium text-gray-900 mb-3">
              Due Date
            </h3>
            {editing ? (
              <input
                type="datetime-local"
                value={editForm.due_date}
                onChange={(e) =>
                  setEditForm({ ...editForm, due_date: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
              />
            ) : task.due_date ? (
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <Calendar className="h-4 w-4" />
                {new Date(task.due_date).toLocaleDateString()}
              </div>
            ) : (
              <p className="text-sm text-gray-500 italic">No due date set</p>
            )}
          </div>

          {/* Priority */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-sm font-medium text-gray-900 mb-3">
              Priority
            </h3>
            {editing ? (
              <div className="space-y-2">
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={editForm.priority ?? ""}
                  onChange={(e) => {
                    const value =
                      e.target.value === ""
                        ? undefined
                        : parseInt(e.target.value, 10);
                    if (value === undefined || (value >= 1 && value <= 10)) {
                      setEditForm({ ...editForm, priority: value });
                    }
                  }}
                  placeholder="1 (lowest) to 10 (highest)"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
                />
                <p className="text-xs text-gray-500">
                  Enter a value from 1 (lowest) to 10 (highest), or leave empty
                </p>
              </div>
            ) : task.priority ? (
              <div className="flex items-center gap-2 text-sm">
                <Flag className={`h-4 w-4 ${
                  task.priority >= 8 ? "text-red-500" :
                  task.priority >= 5 ? "text-orange-500" :
                  "text-yellow-500"
                }`} />
                <span className="text-gray-700 font-medium">
                  Priority {task.priority}
                </span>
              </div>
            ) : (
              <p className="text-sm text-gray-500 italic">No priority set</p>
            )}
          </div>

          {/* Notes */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Notes</h3>
            {editing ? (
              <textarea
                value={editForm.notes}
                onChange={(e) =>
                  setEditForm({ ...editForm, notes: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 resize-none text-sm"
                rows={3}
                placeholder="Add notes..."
              />
            ) : task.notes ? (
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {task.notes}
              </p>
            ) : (
              <p className="text-sm text-gray-500 italic">No notes</p>
            )}
          </div>

          {/* Created Date */}
          {task.created_at && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-sm font-medium text-gray-900 mb-3">
                Created
              </h3>
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <Clock className="h-4 w-4" />
                {new Date(task.created_at).toLocaleString()}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Sub-task Creation Modal */}
      <CreateSubTaskModal
        isOpen={showSubTaskModal}
        onClose={() => setShowSubTaskModal(false)}
        onSubmit={addSubtask}
        projectMembers={projectMembers}
        loading={creatingSubTask}
      />

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={confirmDialog.isOpen}
        onClose={() => setConfirmDialog({ ...confirmDialog, isOpen: false })}
        onConfirm={confirmDialog.onConfirm}
        title={confirmDialog.title}
        description={confirmDialog.description}
        variant={confirmDialog.variant}
        confirmText="Confirm"
      />

      {/* Delete File Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={deleteConfirmDialog.isOpen}
        onClose={() => setDeleteConfirmDialog({ isOpen: false, file: null })}
        onConfirm={handleDeleteConfirm}
        title="Delete File"
        description={`Are you sure you want to delete "${deleteConfirmDialog.file?.original_filename}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="destructive"
      />

      {/* Error Dialog */}
      <Dialog open={errorDialog.isOpen} onOpenChange={(open) => setErrorDialog({ isOpen: open, message: "" })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Error</DialogTitle>
            <DialogDescription>{errorDialog.message}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button onClick={() => setErrorDialog({ isOpen: false, message: "" })}>
              OK
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function TaskDetailSkeleton() {
  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header Skeleton */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <div>
            <Skeleton className="h-8 w-64 mb-2" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Skeleton className="h-10 w-10" />
          <Skeleton className="h-10 w-10" />
        </div>
      </div>

      {/* Content Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Description Skeleton */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <Skeleton className="h-6 w-24 mb-4" />
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-3/4 mb-2" />
            <Skeleton className="h-4 w-1/2" />
          </div>

          {/* Comments Skeleton */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <Skeleton className="h-6 w-20 mb-4" />
            <div className="space-y-4">
              <div className="flex gap-3">
                <Skeleton className="w-8 h-8 rounded-full" />
                <div className="flex-1">
                  <Skeleton className="h-16 w-full mb-2" />
                  <Skeleton className="h-8 w-20 ml-auto" />
                </div>
              </div>
            </div>
          </div>

          {/* Sub-tasks Skeleton */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <Skeleton className="h-6 w-20" />
              <Skeleton className="h-8 w-24" />
            </div>
            <div className="text-center py-8">
              <Skeleton className="h-8 w-8 mx-auto mb-2" />
              <Skeleton className="h-4 w-32 mx-auto mb-1" />
              <Skeleton className="h-3 w-48 mx-auto" />
            </div>
          </div>

          {/* Files Skeleton */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <Skeleton className="h-6 w-12" />
              <Skeleton className="h-8 w-24" />
            </div>
            <div className="text-center py-8">
              <Skeleton className="h-8 w-8 mx-auto mb-2" />
              <Skeleton className="h-4 w-32 mx-auto mb-1" />
              <Skeleton className="h-3 w-40 mx-auto" />
            </div>
          </div>
        </div>

        {/* Sidebar Skeleton */}
        <div className="space-y-6">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="bg-white rounded-lg border border-gray-200 p-6"
            >
              <Skeleton className="h-4 w-16 mb-3" />
              <Skeleton className="h-6 w-20" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
