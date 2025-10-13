"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import { X, Calendar as CalendarIcon, Plus, Trash2 } from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { User } from "@/lib/api";

interface CreateSubTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (subtaskData: SubTaskFormData) => Promise<void>;
  projectMembers: User[];
  loading?: boolean;
}

interface SubTaskFormData {
  title: string;
  description: string;
  status: "todo" | "in_progress" | "completed" | "blocked";
  due_date?: string;
  assignee_ids: string[];
  tags: string[];
  notes: string;
}

export default function CreateSubTaskModal({
  isOpen,
  onClose,
  onSubmit,
  projectMembers,
  loading = false,
}: CreateSubTaskModalProps) {
  const [formData, setFormData] = useState<SubTaskFormData>({
    title: "",
    description: "",
    status: "todo",
    due_date: undefined,
    assignee_ids: [],
    tags: [],
    notes: "",
  });

  const [newTag, setNewTag] = useState("");
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      status: "todo",
      due_date: undefined,
      assignee_ids: [],
      tags: [],
      notes: "",
    });
    setNewTag("");
    setErrors({});
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = "Title is required";
    }

    if (formData.assignee_ids.length > 5) {
      newErrors.assignees = "Maximum 5 assignees allowed";
    }

    if (formData.tags.length > 5) {
      newErrors.tags = "Maximum 5 tags allowed";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    try {
      await onSubmit(formData);
      handleClose();
    } catch (error) {
      console.error("Error creating sub-task:", error);
    }
  };

  const addTag = () => {
    if (
      newTag.trim() &&
      formData.tags.length < 5 &&
      !formData.tags.includes(newTag.trim())
    ) {
      setFormData({
        ...formData,
        tags: [...formData.tags, newTag.trim()],
      });
      setNewTag("");
    }
  };

  const removeTag = (tagToRemove: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter((tag) => tag !== tagToRemove),
    });
  };

  const toggleAssignee = (userId: string) => {
    if (formData.assignee_ids.includes(userId)) {
      setFormData({
        ...formData,
        assignee_ids: formData.assignee_ids.filter((id) => id !== userId),
      });
    } else if (formData.assignee_ids.length < 5) {
      setFormData({
        ...formData,
        assignee_ids: [...formData.assignee_ids, userId],
      });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Create Sub-task
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Form */}
        <div className="flex-1 p-6 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100 hover:scrollbar-thumb-gray-400">
          <form onSubmit={handleSubmit} className="space-y-6 pb-4">
            {/* Title */}
            <div>
              <Label
                htmlFor="title"
                className="text-sm font-medium text-gray-700"
              >
                Title *
              </Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
                placeholder="Enter sub-task title"
                className={cn("mt-1", errors.title && "border-red-500")}
              />
              {errors.title && (
                <p className="text-red-500 text-xs mt-1">{errors.title}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <Label
                htmlFor="description"
                className="text-sm font-medium text-gray-700"
              >
                Description
              </Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="Enter sub-task description"
                rows={3}
                className="mt-1"
              />
            </div>

            {/* Status */}
            <div>
              <Label
                htmlFor="status"
                className="text-sm font-medium text-gray-700"
              >
                Status
              </Label>
              <Select
                value={formData.status}
                onValueChange={(value: SubTaskFormData["status"]) =>
                  setFormData({ ...formData, status: value })
                }
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todo">To Do</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="blocked">Blocked</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Due Date & Time */}
            <div>
              <Label className="text-sm font-medium text-gray-700">
                Due Date & Time
              </Label>
              <div className="flex gap-2 mt-1">
                <Popover open={showDatePicker} onOpenChange={setShowDatePicker}>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "flex-1 justify-start text-left font-normal",
                        !formData.due_date && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {formData.due_date ? (
                        format(new Date(formData.due_date), "PPP")
                      ) : (
                        <span>Pick a date</span>
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={
                        formData.due_date
                          ? new Date(formData.due_date)
                          : undefined
                      }
                      onSelect={(date) => {
                        if (date) {
                          const currentDateTime = formData.due_date
                            ? new Date(formData.due_date)
                            : new Date();
                          const newDateTime = new Date(
                            date.getFullYear(),
                            date.getMonth(),
                            date.getDate(),
                            currentDateTime.getHours(),
                            currentDateTime.getMinutes()
                          );
                          setFormData({
                            ...formData,
                            due_date: newDateTime.toISOString(),
                          });
                        } else {
                          setFormData({
                            ...formData,
                            due_date: undefined,
                          });
                        }
                        setShowDatePicker(false);
                      }}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
                <Input
                  type="time"
                  value={
                    formData.due_date
                      ? new Date(formData.due_date).toTimeString().slice(0, 5)
                      : ""
                  }
                  onChange={(e) => {
                    if (formData.due_date && e.target.value) {
                      const [hours, minutes] = e.target.value.split(":");
                      const currentDate = new Date(formData.due_date);
                      const newDateTime = new Date(
                        currentDate.getFullYear(),
                        currentDate.getMonth(),
                        currentDate.getDate(),
                        parseInt(hours),
                        parseInt(minutes)
                      );
                      setFormData({
                        ...formData,
                        due_date: newDateTime.toISOString(),
                      });
                    }
                  }}
                  className="w-32"
                />
              </div>
            </div>

            {/* Assignees */}
            <div>
              <Label className="text-sm font-medium text-gray-700">
                Assignees ({formData.assignee_ids.length}/5)
              </Label>
              <div className="mt-2 space-y-2">
                {projectMembers.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center justify-between p-2 border border-gray-200 rounded-md"
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-white text-xs font-medium">
                        {member.display_name?.charAt(0) ||
                          member.email?.charAt(0) ||
                          "U"}
                      </div>
                      <span className="text-sm text-gray-900">
                        {member.display_name ||
                          member.email?.split("@")[0] ||
                          "Unknown"}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => toggleAssignee(member.id)}
                      disabled={
                        !formData.assignee_ids.includes(member.id) &&
                        formData.assignee_ids.length >= 5
                      }
                      className={cn(
                        "px-3 py-1 text-xs rounded-md transition-colors",
                        formData.assignee_ids.includes(member.id)
                          ? "bg-blue-600 text-white hover:bg-blue-700"
                          : "bg-gray-100 text-gray-600 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                      )}
                    >
                      {formData.assignee_ids.includes(member.id)
                        ? "Assigned"
                        : "Assign"}
                    </button>
                  </div>
                ))}
              </div>
              {errors.assignees && (
                <p className="text-red-500 text-xs mt-1">{errors.assignees}</p>
              )}
            </div>

            {/* Tags */}
            <div>
              <Label className="text-sm font-medium text-gray-700">
                Tags ({formData.tags.length}/5)
              </Label>
              <div className="mt-2 space-y-2">
                <div className="flex gap-2">
                  <Input
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    placeholder="Add a tag"
                    className="flex-1"
                    onKeyPress={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        addTag();
                      }
                    }}
                  />
                  <Button
                    type="button"
                    onClick={addTag}
                    disabled={
                      !newTag.trim() ||
                      formData.tags.length >= 5 ||
                      formData.tags.includes(newTag.trim())
                    }
                    size="sm"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                {formData.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {formData.tags.map((tag) => (
                      <Badge
                        key={tag}
                        variant="secondary"
                        className="flex items-center gap-1"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => removeTag(tag)}
                          className="ml-1 hover:text-red-600"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
              {errors.tags && (
                <p className="text-red-500 text-xs mt-1">{errors.tags}</p>
              )}
            </div>

            {/* Notes */}
            <div>
              <Label
                htmlFor="notes"
                className="text-sm font-medium text-gray-700"
              >
                Notes
              </Label>
              <Textarea
                id="notes"
                value={formData.notes}
                onChange={(e) =>
                  setFormData({ ...formData, notes: e.target.value })
                }
                placeholder="Add any additional notes"
                rows={3}
                className="mt-1"
              />
            </div>
          </form>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={loading || !formData.title.trim()}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {loading ? "Creating..." : "Create Sub-task"}
          </Button>
        </div>
      </div>
    </div>
  );
}
