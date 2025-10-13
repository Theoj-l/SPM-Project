"use client";

import { useState } from "react";
import { X, FileText, Users, AlertCircle } from "lucide-react";
import { User } from "@/lib/api";
import AssigneeSelector from "./AssigneeSelector";
import { DatePicker } from "@/components/ui/date-picker";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (taskData: TaskFormData) => Promise<void>;
  users: User[];
  isLoading?: boolean;
}

export interface TaskFormData {
  title: string;
  description: string;
  due_date: string;
  notes: string;
  assignee_ids: string[];
  status: "todo" | "in_progress" | "completed" | "blocked";
  tags: string[];
  recurring?: {
    enabled: boolean;
    frequency: "daily" | "weekly" | "monthly" | "yearly";
    interval: number; // Every X days/weeks/months/years
    end_date?: string; // Optional end date for recurring tasks
  };
}

export default function CreateTaskModal({
  isOpen,
  onClose,
  onSubmit,
  users,
  isLoading = false,
}: CreateTaskModalProps) {
  const [formData, setFormData] = useState<TaskFormData>({
    title: "",
    description: "",
    due_date: "",
    notes: "",
    assignee_ids: [],
    status: "todo",
    tags: [],
    recurring: {
      enabled: false,
      frequency: "weekly",
      interval: 1,
    },
  });
  const [dueDate, setDueDate] = useState<Date | undefined>(undefined);
  const [recurringEndDate, setRecurringEndDate] = useState<Date | undefined>(
    undefined
  );
  const [tagInput, setTagInput] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleInputChange = (
    field: keyof TaskFormData,
    value: string | string[]
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: "",
      }));
    }
  };

  const addTag = () => {
    const tag = tagInput.trim();
    if (tag && !formData.tags.includes(tag) && formData.tags.length < 5) {
      setFormData((prev) => ({
        ...prev,
        tags: [...prev.tags, tag],
      }));
      setTagInput("");
    }
  };

  const removeTag = (tagToRemove: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags.filter((tag) => tag !== tagToRemove),
    }));
  };

  const handleTagKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addTag();
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = "Title is required";
    }

    if (dueDate && dueDate < new Date(new Date().setHours(0, 0, 0, 0))) {
      newErrors.due_date = "Due date cannot be in the past";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      const taskData = {
        ...formData,
        due_date: dueDate ? dueDate.toISOString().split("T")[0] : "",
        recurring: formData.recurring?.enabled
          ? {
              ...formData.recurring,
              end_date: recurringEndDate
                ? recurringEndDate.toISOString().split("T")[0]
                : undefined,
            }
          : undefined,
      };
      await onSubmit(taskData);
      // Reset form on success
      setFormData({
        title: "",
        description: "",
        due_date: "",
        notes: "",
        assignee_ids: [],
        status: "todo",
        tags: [],
        recurring: {
          enabled: false,
          frequency: "weekly",
          interval: 1,
        },
      });
      setDueDate(undefined);
      setRecurringEndDate(undefined);
      setTagInput("");
      setErrors({});
    } catch (error) {
      console.error("Failed to create task:", error);
    }
  };

  const handleClose = () => {
    setFormData({
      title: "",
      description: "",
      due_date: "",
      notes: "",
      assignee_ids: [],
      status: "todo",
      tags: [],
      recurring: {
        enabled: false,
        frequency: "weekly",
        interval: 1,
      },
    });
    setDueDate(undefined);
    setRecurringEndDate(undefined);
    setTagInput("");
    setErrors({});
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 flex-shrink-0">
          <h2 className="text-xl font-semibold text-gray-900">
            Create New Task
          </h2>
          <button
            type="button"
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        {/* Scrollable Form Content */}
        <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100 hover:scrollbar-thumb-gray-400">
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Task Title *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => handleInputChange("title", e.target.value)}
                placeholder="Enter task title"
                className={`w-full px-3 py-2 border rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.title ? "border-red-300" : "border-gray-300"
                }`}
                autoFocus
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                  <AlertCircle className="h-4 w-4" />
                  {errors.title}
                </p>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <FileText className="h-4 w-4 inline mr-1" />
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) =>
                  handleInputChange("description", e.target.value)
                }
                placeholder="Enter task description"
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 resize-none"
              />
            </div>

            {/* Due Date and Status */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="due-date"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Due Date & Time
                </label>
                <DatePicker
                  value={dueDate}
                  onChange={setDueDate}
                  placeholder="Select due date"
                  className={errors.due_date ? "border-red-300" : ""}
                  id="due-date"
                  showTime={true}
                />
                {errors.due_date && (
                  <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                    <AlertCircle className="h-4 w-4" />
                    {errors.due_date}
                  </p>
                )}
              </div>

              <div>
                <label
                  htmlFor="status"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Status
                </label>
                <Select
                  value={formData.status}
                  onValueChange={(value) =>
                    handleInputChange("status", value as TaskFormData["status"])
                  }
                >
                  <SelectTrigger id="status" className="w-full">
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todo">To do</SelectItem>
                    <SelectItem value="in_progress">In progress</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="blocked">Blocked</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Assignees */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Users className="h-4 w-4 inline mr-1" />
                Assignees
              </label>
              <AssigneeSelector
                users={users}
                selectedUserIds={formData.assignee_ids}
                onSelectionChange={(assigneeIds) =>
                  handleInputChange("assignee_ids", assigneeIds)
                }
                maxAssignees={5}
                placeholder="Select project members (optional)"
              />
              {users.length === 0 && (
                <div className="text-xs text-orange-600 bg-orange-50 p-2 rounded mt-2">
                  No project members available. Add members to the project first
                  to assign tasks.
                </div>
              )}
              {users.length > 0 && (
                <div className="text-xs text-blue-600 bg-blue-50 p-2 rounded mt-2">
                  💡 You can assign yourself and other project members to tasks.
                </div>
              )}
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <FileText className="h-4 w-4 inline mr-1" />
                Notes
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => handleInputChange("notes", e.target.value)}
                placeholder="Additional notes or comments"
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 resize-none"
              />
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tags ({formData.tags.length}/5)
              </label>
              <div className="space-y-2">
                {/* Tag Input */}
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyPress={handleTagKeyPress}
                    placeholder="Add a tag..."
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    disabled={formData.tags.length >= 5}
                  />
                  <button
                    type="button"
                    onClick={addTag}
                    disabled={
                      !tagInput.trim() ||
                      formData.tags.includes(tagInput.trim()) ||
                      formData.tags.length >= 5
                    }
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                  >
                    Add
                  </button>
                </div>

                {/* Tags Display */}
                {formData.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {formData.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => removeTag(tag)}
                          className="ml-1 text-blue-600 hover:text-blue-800"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}

                {formData.tags.length >= 5 && (
                  <p className="text-xs text-gray-500">
                    Maximum 5 tags allowed
                  </p>
                )}
              </div>
            </div>

            {/* Recurring */}
            <div className="border-t pt-4">
              <div className="flex items-center gap-2 mb-3">
                <input
                  type="checkbox"
                  id="recurring-enabled"
                  checked={formData.recurring?.enabled || false}
                  onChange={(e) => {
                    setFormData({
                      ...formData,
                      recurring: {
                        ...formData.recurring,
                        enabled: e.target.checked,
                        frequency: formData.recurring?.frequency || "weekly",
                        interval: formData.recurring?.interval || 1,
                      },
                    });
                  }}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label
                  htmlFor="recurring-enabled"
                  className="text-sm font-medium text-gray-700"
                >
                  Make this a recurring task
                </label>
              </div>

              {formData.recurring?.enabled && (
                <div className="space-y-4 pl-6 border-l-2 border-blue-200">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Frequency
                      </label>
                      <Select
                        value={formData.recurring?.frequency || "weekly"}
                        onValueChange={(value) => {
                          setFormData({
                            ...formData,
                            recurring: {
                              enabled: formData.recurring?.enabled || false,
                              frequency: value as
                                | "daily"
                                | "weekly"
                                | "monthly"
                                | "yearly",
                              interval: formData.recurring?.interval || 1,
                            },
                          });
                        }}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="daily">Daily</SelectItem>
                          <SelectItem value="weekly">Weekly</SelectItem>
                          <SelectItem value="monthly">Monthly</SelectItem>
                          <SelectItem value="yearly">Yearly</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Every
                      </label>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          min="1"
                          max="365"
                          value={formData.recurring?.interval || 1}
                          onChange={(e) => {
                            setFormData({
                              ...formData,
                              recurring: {
                                enabled: formData.recurring?.enabled || false,
                                frequency:
                                  formData.recurring?.frequency || "weekly",
                                interval: parseInt(e.target.value) || 1,
                              },
                            });
                          }}
                          className="w-20 px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                        />
                        <span className="text-sm text-gray-600">
                          {formData.recurring?.frequency === "daily" &&
                            "day(s)"}
                          {formData.recurring?.frequency === "weekly" &&
                            "week(s)"}
                          {formData.recurring?.frequency === "monthly" &&
                            "month(s)"}
                          {formData.recurring?.frequency === "yearly" &&
                            "year(s)"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      End Date (Optional)
                    </label>
                    <DatePicker
                      value={recurringEndDate}
                      onChange={setRecurringEndDate}
                      placeholder="Select end date (leave empty for no end)"
                      className="w-full"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Leave empty to create recurring tasks indefinitely
                    </p>
                  </div>
                </div>
              )}
            </div>
          </form>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 p-6 border-t border-gray-200 flex-shrink-0">
          <button
            type="button"
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={isLoading}
            onClick={handleSubmit}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? "Creating..." : "Create Task"}
          </button>
        </div>
      </div>
    </div>
  );
}
