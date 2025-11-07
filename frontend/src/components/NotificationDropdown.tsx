"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Bell } from "lucide-react";
import { NotificationsAPI, Notification } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";

interface NotificationDropdownProps {
  className?: string;
}

export default function NotificationDropdown({ className }: NotificationDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const data = await NotificationsAPI.list(5, 0, false); // Get 5 most recent unread
      setNotifications(data);
    } catch (err: unknown) {
      console.error("Failed to load notifications:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadUnreadCount = async () => {
    try {
      const result = await NotificationsAPI.getUnreadCount();
      setUnreadCount(result.count);
    } catch (err: unknown) {
      console.error("Failed to load unread count:", err);
    }
  };

  useEffect(() => {
    loadUnreadCount();
    loadNotifications();
    
    // Poll for new notifications every 30 seconds
    const interval = setInterval(() => {
      loadUnreadCount();
      if (isOpen) {
        loadNotifications();
      }
    }, 30000);

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      loadNotifications(); // Reload when opening
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  const handleNotificationClick = async (notification: Notification) => {
    if (!notification.read) {
      try {
        await NotificationsAPI.markAsRead(notification.id);
        setNotifications((prev) =>
          prev.map((n) => (n.id === notification.id ? { ...n, read: true } : n))
        );
        setUnreadCount((prev) => Math.max(0, prev - 1));
      } catch (err: unknown) {
        console.error("Failed to mark notification as read:", err);
      }
    }

    setIsOpen(false);
    if (notification.link_url) {
      router.push(notification.link_url);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await NotificationsAPI.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (err: unknown) {
      console.error("Failed to mark all as read:", err);
    }
  };

  const getNotificationIcon = (type: Notification["type"]) => {
    const iconStyles: Record<Notification["type"], string> = {
      task_update: "bg-blue-500",
      mention: "bg-purple-500",
      task_assigned: "bg-green-500",
      deadline_reminder: "bg-yellow-500",
      overdue: "bg-red-500",
      daily_digest: "bg-indigo-500",
    };
    return iconStyles[type] || "bg-gray-500";
  };

  const formatTime = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return dateString;
    }
  };

  return (
    <div className={cn("relative", className)} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full transition-colors"
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50 max-h-96 overflow-hidden flex flex-col">
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllAsRead}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="overflow-y-auto flex-1">
            {loading ? (
              <div className="p-4 text-center text-sm text-gray-500">Loading...</div>
            ) : notifications.length === 0 ? (
              <div className="p-4 text-center text-sm text-gray-500">
                No new notifications
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    onClick={() => handleNotificationClick(notification)}
                    className={cn(
                      "p-3 hover:bg-gray-50 cursor-pointer transition-colors",
                      !notification.read && "bg-blue-50"
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={cn(
                          "w-2 h-2 rounded-full mt-2 flex-shrink-0",
                          notification.read ? "bg-gray-300" : getNotificationIcon(notification.type)
                        )}
                      />
                      <div className="flex-1 min-w-0">
                        <p
                          className={cn(
                            "text-sm",
                            !notification.read ? "font-semibold text-gray-900" : "text-gray-700"
                          )}
                        >
                          {notification.title}
                        </p>
                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                          {notification.message}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          {formatTime(notification.created_at)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="border-t border-gray-200 p-2">
            <button
              onClick={() => {
                setIsOpen(false);
                router.push("/notifications");
              }}
              className="w-full text-center text-xs text-blue-600 hover:text-blue-800 py-2"
            >
              View all notifications
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

