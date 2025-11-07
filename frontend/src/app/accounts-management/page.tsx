"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { AuthAPI, LockedAccount } from "@/lib/api";
import { isAdmin } from "@/utils/role-utils";
import { ArrowLeft, Lock, Unlock, Clock, AlertCircle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import Link from "next/link";
import { toast } from "sonner";

export default function AccountsManagementPage() {
  const { user } = useAuth();
  const [lockedAccounts, setLockedAccounts] = useState<LockedAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [unlockingEmail, setUnlockingEmail] = useState<string | null>(null);

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

  // Load locked accounts
  const loadLockedAccounts = async () => {
    try {
      setLoading(true);
      const response = await AuthAPI.listLockedAccounts();
      setLockedAccounts(response.data?.accounts || []);
    } catch (err: unknown) {
      setError("Failed to load locked accounts");
      console.error("Error loading locked accounts:", err);
    } finally {
      setLoading(false);
    }
  };

  // Unlock an account
  const unlockAccount = async (email: string) => {
    try {
      setUnlockingEmail(email);
      await AuthAPI.unlockAccount(email);
      toast.success(`Account ${email} has been unlocked successfully`);
      await loadLockedAccounts(); // Reload to update the list
    } catch (err: unknown) {
      toast.error(
        `Failed to unlock account: ${err instanceof Error ? err.message : "Unknown error"}`
      );
    } finally {
      setUnlockingEmail(null);
    }
  };

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  // Check if lockout has expired
  const isLockoutExpired = (lockedUntil: string) => {
    return new Date(lockedUntil) < new Date();
  };

  useEffect(() => {
    if (isAdmin(user)) {
      loadLockedAccounts();
    }
  }, [user]);

  // Check if user is admin
  if (!isAdmin(user)) {
    return (
      <div className="max-w-6xl mx-auto p-4">
        <div className="text-center py-12">
          <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Access Denied
          </h3>
          <p className="text-gray-500">
            You don&apos;t have permission to access this page. Admin role required.
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return <LockedAccountsSkeleton />;
  }

  return (
    <div className="max-w-6xl mx-auto p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              Accounts Management
            </h1>
            <p className="text-sm text-gray-600">
              Manage locked accounts and unlock users
            </p>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Locked Accounts List */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Lock className="h-5 w-5 text-gray-600" />
          <h2 className="text-lg font-semibold text-gray-900">
            Locked Accounts
          </h2>
          <span className="text-sm text-gray-500">
            ({lockedAccounts.length} locked)
          </span>
        </div>

        {lockedAccounts.length === 0 ? (
          <div className="text-center py-6 bg-gray-50 rounded-lg">
            <Unlock className="h-6 w-6 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-500">No locked accounts</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="divide-y divide-gray-200">
              {lockedAccounts.map((account) => (
                <div
                  key={account.email}
                  className="p-3 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1.5">
                        <h3 className="text-sm font-medium text-gray-900 truncate">
                          {account.email}
                        </h3>
                        <span
                          className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium ${
                            isLockoutExpired(account.locked_until)
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-red-100 text-red-800"
                          }`}
                        >
                          <Lock className="h-3 w-3 mr-1" />
                          {isLockoutExpired(account.locked_until)
                            ? "Expired"
                            : "Locked"}
                        </span>
                      </div>

                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Locked at: {formatDate(account.locked_at)}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Locked until: {formatDate(account.locked_until)}
                        </span>
                        {account.lockout_reason && (
                          <span className="flex items-center gap-1">
                            <AlertCircle className="h-3 w-3" />
                            {account.lockout_reason}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 ml-3">
                      <button
                        onClick={() => {
                          setConfirmDialog({
                            isOpen: true,
                            title: "Unlock Account",
                            description: `Are you sure you want to unlock the account "${account.email}"?`,
                            variant: "default",
                            onConfirm: () => unlockAccount(account.email),
                          });
                        }}
                        disabled={unlockingEmail === account.email}
                        className="flex items-center gap-1 px-2.5 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        <Unlock className="h-3 w-3" />
                        {unlockingEmail === account.email
                          ? "Unlocking..."
                          : "Unlock"}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

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
    </div>
  );
}

// Skeleton component for loading state
function LockedAccountsSkeleton() {
  return (
    <div className="max-w-6xl mx-auto p-4">
      <div className="flex items-center gap-3 mb-4">
        <Skeleton className="h-9 w-9" />
        <div>
          <Skeleton className="h-7 w-48 mb-1.5" />
          <Skeleton className="h-3.5 w-64" />
        </div>
      </div>

      <div>
        <div className="flex items-center gap-2 mb-3">
          <Skeleton className="h-5 w-5" />
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-16" />
        </div>
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="p-3">
            <Skeleton className="h-4 w-full mb-1.5" />
            <Skeleton className="h-3 w-3/4" />
          </div>
        </div>
      </div>
    </div>
  );
}
