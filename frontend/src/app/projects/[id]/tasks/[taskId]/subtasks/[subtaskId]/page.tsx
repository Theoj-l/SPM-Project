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
import {
  ArrowLeft,
  Edit,
  Trash2,
  MessageSquare,
  Paperclip,
  Plus,
  Calendar,
  User as UserIcon,
  Clock,
  AlertCircle,
  Save,
  X,
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
    if (
      dateString &&
      !dateString.endsWith("Z") &&
      !dateString.includes("+") &&
      !dateString.includes("-", 10)
    ) {
      // Check if it's a valid ISO format without timezone (e.g., "2023-10-27T12:57:00")
      if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$/.test(dateString)) {
        normalizedDateString = dateString + "Z";
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
}: {
  comment: Comment;
  user: { id: string; email: string; full_name?: string } | null;
  onReply: (parentCommentId: string, replyText: string) => void;
  onDelete: (commentId: string) => void;
  onEdit: (commentId: string, content: string) => void;
  isAdmin: boolean;
  isManager: boolean;
  projectMembers: User[];
}) {
  const [isReplying, setIsReplying] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(comment.content);
  const isCreator = user?.id === comment.user_id;
  const canDelete = isCreator || isAdmin;
  const canEdit = isCreator;

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
      setIsReplying(false);
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
    <div className="border-l-2 border-gray-200 pl-4 mb-4">
      <div className="bg-white rounded-lg p-4 shadow-sm border">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
              {comment.user_display_name?.charAt(0) ||
                comment.user_email?.charAt(0) ||
                "U"}
            </div>
            <div>
              <p className="font-medium text-gray-900">
                {comment.user_display_name ||
                  comment.user_email?.split("@")[0] ||
                  "Unknown"}
              </p>
              <p className="text-sm text-gray-500">
                {formatSingaporeTime(comment.created_at)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {canEdit && !isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="text-blue-500 hover:text-blue-700 p-1"
                title="Edit comment"
              >
                <Edit className="h-4 w-4" />
              </button>
            )}
            {canDelete && (
              <button
                onClick={() => onDelete(comment.id)}
                className="text-red-500 hover:text-red-700 p-1"
                title={
                  isCreator ? "Delete your comment" : "Delete comment (Admin)"
                }
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
        {isEditing ? (
          <div className="mt-3">
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={3}
              autoFocus
            />
            <div className="flex space-x-2 mt-2">
              <button
                onClick={handleEdit}
                disabled={!editText.trim() || editText === comment.content}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                Save
              </button>
              <button
                onClick={handleCancelEdit}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <p className="mt-3 text-gray-700 whitespace-pre-wrap">
            {comment.content
              .split(/(@[\w\s]+?)(?=\s|$|[.,!?;:])/)
              .map((part, index) => {
                if (part.startsWith("@")) {
                  return (
                    <span
                      key={index}
                      className="bg-blue-100 text-blue-700 px-1 rounded font-medium"
                    >
                      {part}
                    </span>
                  );
                }
                return <span key={index}>{part}</span>;
              })}
          </p>
        )}
        {!isEditing && (
          <div className="mt-3 flex items-center space-x-4">
            <button
              onClick={() => setIsReplying(!isReplying)}
              className="text-blue-500 hover:text-blue-700 text-sm flex items-center space-x-1"
            >
              <MessageSquare className="h-4 w-4" />
              <span>Reply</span>
            </button>
          </div>
        )}
        {isReplying && (
          <div className="mt-3 space-y-2">
            <textarea
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder="Write a reply..."
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={3}
            />
            <div className="flex space-x-2">
              <button
                onClick={handleReply}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 text-sm"
              >
                Reply
              </button>
              <button
                onClick={() => {
                  setIsReplying(false);
                  setReplyText("");
                }}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
      {comment.replies && comment.replies.length > 0 && (
        <div className="mt-4 space-y-2">
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
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function SubTaskDetailPage() {
  const { id: projectId, taskId, subtaskId } = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const [project, setProject] = useState<Project | null>(null);
  const [task, setTask] = useState<Task | null>(null);
  const [subtask, setSubtask] = useState<SubTask | null>(null);
  const [projectMembers, setProjectMembers] = useState<User[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [files, setFiles] = useState<TaskFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [newComment, setNewComment] = useState("");
  const [addingComment, setAddingComment] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
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

  // Form data for editing
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    status: "todo" as "todo" | "in_progress" | "completed" | "blocked",
    assignee_ids: [] as string[],
    due_date: "",
    notes: "",
    tags: [] as string[],
  });

  const isProjectOwner = project?.owner_id === user?.id;
  const isTaskAssignee = subtask?.assignee_ids?.includes(user?.id || "");
  const canEdit =
    isProjectOwner || isTaskAssignee || canAdminManage(user) || isManager(user);

  useEffect(() => {
    if (projectId && taskId && subtaskId) {
      loadData();
    }
  }, [projectId, taskId, subtaskId]);

  const loadData = async () => {
    try {
      setLoading(true);

      // Load essential data first
      const [taskData, subtaskData, membersData] = await Promise.all([
        TasksAPI.getById(taskId as string),
        SubTasksAPI.getById(subtaskId as string),
        ProjectsAPI.getMembers(projectId as string),
      ]);

      setTask(taskData);
      setSubtask(subtaskData);
      // Convert project members to user format
      const memberUsers: User[] = membersData.map((member) => ({
        id: member.user_id,
        email: member.user_email || "",
        display_name: member.user_display_name || undefined,
        roles: [member.role],
      }));
      setProjectMembers(memberUsers);

      // Try to load project data (optional, since it's failing)
      try {
        const projectData = await ProjectsAPI.getById(projectId as string);
        setProject(projectData);
      } catch (error) {
        console.warn("Could not load project data:", error);
        // Project data is optional for sub-task page
      }

      // Set form data
      setFormData({
        title: subtaskData.title || "",
        description: subtaskData.description || "",
        status: subtaskData.status || "todo",
        assignee_ids: subtaskData.assignee_ids || [],
        due_date: subtaskData.due_date || "",
        notes: subtaskData.notes || "",
        tags: subtaskData.tags || [],
      });

      // Load comments and files
      await Promise.all([loadComments(), loadFiles()]);
    } catch (error) {
      console.error("Error loading data:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadComments = async () => {
    try {
      const commentsData = await CommentsAPI.list(subtaskId as string);
      setComments(commentsData);
    } catch (error) {
      console.error("Error loading comments:", error);
    }
  };

  const loadFiles = async () => {
    try {
      const filesData = await FilesAPI.listForSubtask(subtaskId as string);
      setFiles(filesData);
    } catch (error) {
      console.error("Error loading files:", error);
    }
  };

  const handleSave = async () => {
    // Validate that at least one assignee is selected
    if (!formData.assignee_ids || formData.assignee_ids.length === 0) {
      setError("At least one assignee is required");
      return;
    }

    try {
      setSaving(true);
      setError("");
      await SubTasksAPI.update(subtaskId as string, formData);
      await loadData();
      setEditing(false);
    } catch (error: unknown) {
      setError(
        error instanceof Error ? error.message : "Failed to update subtask"
      );
      console.error("Error saving subtask:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      title: subtask?.title || "",
      description: subtask?.description || "",
      status: subtask?.status || "todo",
      assignee_ids: subtask?.assignee_ids || [],
      due_date: subtask?.due_date || "",
      notes: subtask?.notes || "",
      tags: subtask?.tags || [],
    });
    setEditing(false);
  };

  const addComment = async () => {
    if (!newComment.trim()) return;

    try {
      setAddingComment(true);
      const comment = await CommentsAPI.create(
        subtaskId as string,
        newComment.trim()
      );
      // Ensure comment has proper structure with empty replies array
      const newCommentWithReplies: Comment = {
        ...comment,
        replies: comment.replies || [],
        user_display_name: comment.user_display_name || user?.full_name,
        user_email: comment.user_email || user?.email,
      };
      setComments([...comments, newCommentWithReplies]);
      setNewComment("");
    } catch (error) {
      console.error("Error adding comment:", error);
    } finally {
      setAddingComment(false);
    }
  };

  const addReply = async (parentCommentId: string, replyText: string) => {
    try {
      const reply = await CommentsAPI.create(
        subtaskId as string,
        replyText.trim(),
        parentCommentId
      );

      // Ensure reply has proper structure
      const newReply: Comment = {
        ...reply,
        replies: [],
        user_display_name: reply.user_display_name || user?.full_name,
        user_email: reply.user_email || user?.email,
      };

      // Immediately add reply to parent comment's replies array
      setComments(
        comments.map((comment) => {
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
              replies: comment.replies.map((replyItem) => {
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
        })
      );
    } catch (error) {
      console.error("Error adding reply:", error);
    }
  };

  const deleteComment = async (commentId: string) => {
    const comment =
      comments.find((c) => c.id === commentId) ||
      comments.flatMap((c) => c.replies || []).find((r) => r.id === commentId);

    if (!comment) {
      console.error("Comment not found");
      return;
    }

    const isCreator = user?.id === comment.user_id;
    if (!isCreator && !isAdmin(user)) {
      console.error("Only the comment creator or admin can delete comments");
      return;
    }

    try {
      await CommentsAPI.delete(commentId);
      await loadComments();
    } catch (error) {
      console.error("Error deleting comment:", error);
    }
  };

  const editComment = async (commentId: string, content: string) => {
    const comment =
      comments.find((c) => c.id === commentId) ||
      comments.flatMap((c) => c.replies || []).find((r) => r.id === commentId);

    if (!comment) {
      console.error("Comment not found");
      return;
    }

    if (user?.id !== comment.user_id) {
      console.error("Only the comment creator can edit comments");
      return;
    }

    try {
      await CommentsAPI.update(commentId, content);
      await loadComments();
    } catch (error) {
      console.error("Error updating comment:", error);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploadingFile(true);
      await FilesAPI.uploadForSubtask(subtaskId as string, selectedFile);
      setSelectedFile(null);
      await loadFiles();
    } catch (error) {
      console.error("Error uploading file:", error);
    } finally {
      setUploadingFile(false);
    }
  };

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
    }
  };

  const handleDeleteClick = (file: TaskFile) => {
    setDeleteConfirmDialog({ isOpen: true, file });
  };

  const handleDeleteConfirm = async () => {
    if (!deleteConfirmDialog.file) return;

    try {
      await FilesAPI.delete(deleteConfirmDialog.file.id);
      // Refresh files list
      const updatedFiles = await FilesAPI.listForSubtask(subtaskId as string);
      setFiles(updatedFiles);
      setDeleteConfirmDialog({ isOpen: false, file: null });
    } catch (error) {
      console.error("Error deleting file:", error);
      setDeleteConfirmDialog({ isOpen: false, file: null });
      setErrorDialog({
        isOpen: true,
        message:
          "Failed to delete file. You may only delete files you uploaded.",
      });
    }
  };

  const getStatusColor = (status: string) => {
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

  const getStatusDisplay = (status: string) => {
    switch (status) {
      case "todo":
        return "To Do";
      case "in_progress":
        return "In Progress";
      case "completed":
        return "Completed";
      case "blocked":
        return "Blocked";
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="mb-6">
            <Skeleton className="h-8 w-48" />
          </div>
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <Skeleton className="h-8 w-3/4 mb-4" />
            <Skeleton className="h-4 w-1/2 mb-6" />
            <div className="space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!subtask) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-sm border p-6 text-center">
            <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Sub-task not found
            </h2>
            <p className="text-gray-600 mb-4">
              The sub-task you&apos;re looking for doesn&apos;t exist or you
              don&apos;t have access to it.
            </p>
            <button
              onClick={() => router.back()}
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
            >
              Go Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => router.back()}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Back to Task
          </button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {editing ? (
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) =>
                      setFormData({ ...formData, title: e.target.value })
                    }
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                ) : (
                  subtask.title
                )}
              </h1>
              <p className="text-gray-600 mt-1">
                Sub-task of: <span className="font-medium">{task?.title}</span>
              </p>
            </div>
            {canEdit && (
              <div className="flex space-x-2">
                {editing ? (
                  <>
                    <button
                      onClick={handleSave}
                      disabled={saving}
                      className="flex items-center px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50"
                    >
                      <Save className="h-4 w-4 mr-2" />
                      {saving ? "Saving..." : "Save"}
                    </button>
                    <button
                      onClick={handleCancel}
                      className="flex items-center px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                    >
                      <X className="h-4 w-4 mr-2" />
                      Cancel
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setEditing(true)}
                    className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
                  >
                    <Edit className="h-4 w-4 mr-2" />
                    Edit
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Description */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Description
              </h3>
              {editing ? (
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={4}
                  placeholder="Enter sub-task description"
                />
              ) : (
                <p className="text-gray-700">
                  {subtask.description || "No description provided"}
                </p>
              )}
            </div>

            {/* Notes */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Notes
              </h3>
              {editing ? (
                <textarea
                  value={formData.notes}
                  onChange={(e) =>
                    setFormData({ ...formData, notes: e.target.value })
                  }
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={4}
                  placeholder="Enter additional notes"
                />
              ) : (
                <p className="text-gray-700">
                  {subtask.notes || "No notes provided"}
                </p>
              )}
            </div>

            {/* Comments */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Comments
              </h3>
              <div className="space-y-4">
                {comments
                  .filter((comment) => !comment.parent_comment_id)
                  .map((comment) => (
                    <CommentItem
                      key={comment.id}
                      comment={comment}
                      user={user}
                      onReply={addReply}
                      onDelete={deleteComment}
                      onEdit={editComment}
                      isAdmin={isAdmin(user)}
                      isManager={isManager(user)}
                      projectMembers={projectMembers}
                    />
                  ))}
              </div>
              <div className="mt-6 pt-4 border-t">
                <textarea
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Add a comment..."
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={3}
                />
                <div className="mt-3 flex justify-end">
                  <button
                    onClick={addComment}
                    disabled={addingComment || !newComment.trim()}
                    className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
                  >
                    {addingComment ? "Adding..." : "Add Comment"}
                  </button>
                </div>
              </div>
            </div>

            {/* Files */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Files
              </h3>
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
              <div className="mt-4 pt-4 border-t">
                <div className="flex items-center space-x-3">
                  <input
                    type="file"
                    onChange={(e) =>
                      setSelectedFile(e.target.files?.[0] || null)
                    }
                    className="flex-1 p-2 border border-gray-300 rounded-md"
                  />
                  <button
                    onClick={handleFileUpload}
                    disabled={uploadingFile || !selectedFile}
                    className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50"
                  >
                    {uploadingFile ? "Uploading..." : "Upload"}
                  </button>
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  Maximum file size: 50MB
                </p>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Status */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Status
              </h3>
              {editing ? (
                <Select
                  value={formData.status}
                  onValueChange={(
                    value: "todo" | "in_progress" | "completed" | "blocked"
                  ) => setFormData({ ...formData, status: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todo">To Do</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="blocked">Blocked</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <span
                  className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                    subtask.status
                  )}`}
                >
                  {getStatusDisplay(subtask.status)}
                </span>
              )}
            </div>

            {/* Assignees */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Assignees
              </h3>
              {editing ? (
                <AssigneeSelector
                  selectedUserIds={formData.assignee_ids}
                  onSelectionChange={(ids) =>
                    setFormData({ ...formData, assignee_ids: ids })
                  }
                  users={projectMembers}
                  maxAssignees={5}
                />
              ) : (
                <div className="space-y-2">
                  {subtask.assignee_names?.map((name, index) => (
                    <div
                      key={index}
                      className="flex items-center space-x-2 text-sm"
                    >
                      <UserIcon className="h-4 w-4 text-gray-400" />
                      <span>{name}</span>
                    </div>
                  ))}
                  {(!subtask.assignee_names ||
                    subtask.assignee_names.length === 0) && (
                    <p className="text-gray-500 text-sm">No assignees</p>
                  )}
                </div>
              )}
            </div>

            {/* Due Date */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Due Date
              </h3>
              {editing ? (
                <input
                  type="datetime-local"
                  value={
                    formData.due_date
                      ? new Date(formData.due_date).toISOString().slice(0, 16)
                      : ""
                  }
                  onChange={(e) =>
                    setFormData({ ...formData, due_date: e.target.value })
                  }
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              ) : (
                <div className="flex items-center space-x-2 text-sm">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <span>
                    {subtask.due_date
                      ? new Date(subtask.due_date).toLocaleString()
                      : "No due date"}
                  </span>
                </div>
              )}
            </div>

            {/* Tags */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Tags</h3>
              {editing ? (
                <div className="space-y-2">
                  <input
                    type="text"
                    value={formData.tags.join(", ")}
                    onChange={(e) => {
                      const tags = e.target.value
                        .split(",")
                        .map((tag) => tag.trim())
                        .filter((tag) => tag.length > 0)
                        .slice(0, 5);
                      setFormData({ ...formData, tags });
                    }}
                    placeholder="Enter tags separated by commas (max 5)"
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500">
                    {formData.tags.length}/5 tags
                  </p>
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {subtask.tags?.map((tag, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-sm"
                    >
                      {tag}
                    </span>
                  ))}
                  {(!subtask.tags || subtask.tags.length === 0) && (
                    <p className="text-gray-500 text-sm">No tags</p>
                  )}
                </div>
              )}
            </div>

            {/* Created Info */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Created
              </h3>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <Clock className="h-4 w-4" />
                <span>
                  {new Date(subtask.created_at || "").toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
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
      <Dialog
        open={errorDialog.isOpen}
        onOpenChange={(open) => setErrorDialog({ isOpen: open, message: "" })}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Error</DialogTitle>
            <DialogDescription>{errorDialog.message}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              onClick={() => setErrorDialog({ isOpen: false, message: "" })}
            >
              OK
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
