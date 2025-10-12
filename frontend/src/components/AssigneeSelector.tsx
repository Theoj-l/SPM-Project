"use client";

import { useState, useRef, useEffect } from "react";
import { User, X, Plus } from "lucide-react";
import { User as UserType } from "@/lib/api";

interface AssigneeSelectorProps {
  users: UserType[];
  selectedUserIds: string[];
  onSelectionChange: (userIds: string[]) => void;
  maxAssignees?: number;
  placeholder?: string;
}

export default function AssigneeSelector({
  users,
  selectedUserIds,
  onSelectionChange,
  maxAssignees = 5,
  placeholder = "Select assignees...",
}: AssigneeSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Filter users based on search term and exclude already selected users
  const filteredUsers = users.filter(
    (user) =>
      (user.display_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase())) &&
      !selectedUserIds.includes(user.id)
  );

  // Get selected users for display
  const selectedUsers = users.filter((user) =>
    selectedUserIds.includes(user.id)
  );

  const handleUserSelect = (userId: string) => {
    if (selectedUserIds.length < maxAssignees) {
      onSelectionChange([...selectedUserIds, userId]);
    }
    setSearchTerm("");
  };

  const handleUserRemove = (userId: string) => {
    onSelectionChange(selectedUserIds.filter((id) => id !== userId));
  };

  const getUserDisplayName = (user: UserType) => {
    return user.display_name || user.email;
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setSearchTerm("");
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Selected Assignees Display */}
      <div className="min-h-[40px] border border-gray-300 rounded-md p-2 flex flex-wrap gap-1 items-center">
        {selectedUsers.map((user) => (
          <div
            key={user.id}
            className="flex items-center gap-1 bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm"
          >
            <User className="h-3 w-3" />
            <span className="truncate max-w-[120px]">
              {getUserDisplayName(user)}
            </span>
            <button
              type="button"
              onClick={() => handleUserRemove(user.id)}
              className="hover:bg-blue-200 rounded-full p-0.5"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        ))}

        {/* Add Assignee Button */}
        {selectedUserIds.length < maxAssignees && (
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center gap-1 text-gray-500 hover:text-gray-700 px-2 py-1 rounded-full hover:bg-gray-100 text-sm"
          >
            <Plus className="h-3 w-3" />
            <span>Add assignee</span>
          </button>
        )}

        {/* Placeholder when no assignees */}
        {selectedUserIds.length === 0 && (
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="text-gray-400 hover:text-gray-600 text-sm"
          >
            {placeholder}
          </button>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-md shadow-lg z-10 max-h-60 overflow-y-auto">
          {/* Search Input */}
          <div className="p-2 border-b border-gray-200">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search project members..."
              className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              autoFocus
            />
          </div>

          {/* User List */}
          <div className="py-1">
            {filteredUsers.length === 0 ? (
              <div className="px-3 py-2 text-sm text-gray-500">
                {searchTerm
                  ? "No project members found"
                  : "No project members available"}
              </div>
            ) : (
              filteredUsers.map((user) => (
                <button
                  key={user.id}
                  type="button"
                  onClick={() => handleUserSelect(user.id)}
                  className="w-full px-3 py-2 text-left hover:bg-gray-100 flex items-center gap-2 text-sm"
                >
                  <User className="h-4 w-4 text-gray-400" />
                  <div>
                    <div className="font-medium">
                      {getUserDisplayName(user)}
                    </div>
                    <div className="text-xs text-gray-500">{user.email}</div>
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Max Assignees Warning */}
          {selectedUserIds.length >= maxAssignees && (
            <div className="px-3 py-2 text-xs text-orange-600 bg-orange-50 border-t border-gray-200">
              Maximum {maxAssignees} assignees allowed
            </div>
          )}
        </div>
      )}
    </div>
  );
}
