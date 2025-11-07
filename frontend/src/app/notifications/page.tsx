"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { NotificationsAPI, Notification } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";

export default function NotificationsPage() {
  const router = useRouter();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [includeRead, setIncludeRead] = useState(true);
  const limit = 20;

  const loadNotifications = useCallback(async (reset = false) => {
    if (reset) {
      setOffset(0);
      setNotifications([]);
      setLoading(true);
    } else {
      setLoadingMore(true);
    }

    try {
      const currentOffset = reset ? 0 : offset;
      const data = await NotificationsAPI.list(limit, currentOffset, includeRead);
      
      if (reset) {
        setNotifications(data);
      } else {
        setNotifications((prev) => [...prev, ...data]);
      }
      
      setHasMore(data.length === limit);
      setOffset(currentOffset + data.length);
    } catch (err: unknown) {
      console.error("Failed to load notifications:", err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [offset, includeRead, limit]);

  const loadUnreadCount = useCallback(async () => {
    try {
      const result = await NotificationsAPI.getUnreadCount();
      setUnreadCount(result.count);
    } catch (err: unknown) {
      console.error("Failed to load unread count:", err);
    }
  }, []);

  useEffect(() => {
    loadNotifications(true);
    loadUnreadCount();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [includeRead]);

  // Poll for unread count every 30 seconds
  useEffect(() => {
    const interval = setInterval(loadUnreadCount, 30000);
    return () => clearInterval(interval);
  }, [loadUnreadCount]);

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await NotificationsAPI.markAsRead(notificationId);
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n))
      );
      loadUnreadCount();
    } catch (err: unknown) {
      console.error("Failed to mark notification as read:", err);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await NotificationsAPI.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      loadUnreadCount();
    } catch (err: unknown) {
      console.error("Failed to mark all as read:", err);
    }
  };

  const handleNotificationClick = async (notification: Notification) => {
    if (!notification.read) {
      await handleMarkAsRead(notification.id);
    }

    if (notification.link_url) {
      router.push(notification.link_url);
    }
  };

  const getNotificationStyles = (type: Notification["type"], read: boolean) => {
    const baseStyles = read
      ? "bg-gray-50 dark:bg-gray-950/20 border-gray-300 dark:border-gray-700"
      : "";

    const typeStyles: Record<Notification["type"], string> = {
      task_update: read
        ? baseStyles
        : "bg-blue-50 dark:bg-blue-950/20 border-blue-500",
      mention: read
        ? baseStyles
        : "bg-purple-50 dark:bg-purple-950/20 border-purple-500",
      task_assigned: read
        ? baseStyles
        : "bg-green-50 dark:bg-green-950/20 border-green-500",
      deadline_reminder: read
        ? baseStyles
        : "bg-yellow-50 dark:bg-yellow-950/20 border-yellow-500",
      overdue: read
        ? baseStyles
        : "bg-red-50 dark:bg-red-950/20 border-red-500",
      daily_digest: read
        ? baseStyles
        : "bg-indigo-50 dark:bg-indigo-950/20 border-indigo-500",
    };

    return typeStyles[type] || baseStyles;
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
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Notifications</h1>
        <p className="text-muted-foreground">
          Stay updated with your latest notifications
          {unreadCount > 0 && (
            <span className="ml-2 text-primary font-semibold">
              ({unreadCount} unread)
            </span>
          )}
        </p>
      </div>

      <div className="grid gap-6">
        <div className="rounded-lg border bg-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <h2 className="text-xl font-semibold">Recent Notifications</h2>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={includeRead}
                  onChange={(e) => setIncludeRead(e.target.checked)}
                  className="rounded"
                />
                <span>Include read</span>
              </label>
            </div>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllAsRead}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Mark all as read
              </button>
            )}
          </div>

          {loading && notifications.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading notifications...
            </div>
          ) : notifications.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No notifications found
            </div>
          ) : (
            <div className="space-y-4">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  onClick={() => handleNotificationClick(notification)}
                  className={`flex items-start space-x-3 p-3 rounded-lg border-l-4 cursor-pointer hover:bg-opacity-80 transition-colors ${getNotificationStyles(
                    notification.type,
                    notification.read
                  )}`}
                >
                  <div
                    className={`w-2 h-2 rounded-full mt-2 ${
                      notification.read ? "bg-gray-400" : getNotificationIcon(notification.type)
                    }`}
                  ></div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <p
                        className={`font-medium ${
                          !notification.read ? "font-semibold" : ""
                        }`}
                      >
                        {notification.title}
                      </p>
                      {!notification.read && (
                        <span className="ml-2 w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 mt-1"></span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {notification.message}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatTime(notification.created_at)}
                    </p>
                  </div>
                </div>
              ))}

              {hasMore && (
                <div className="text-center pt-4">
                  <button
                    onClick={() => loadNotifications(false)}
                    disabled={loadingMore}
                    className="text-sm text-primary hover:underline disabled:opacity-50"
                  >
                    {loadingMore ? "Loading..." : "Load more"}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
