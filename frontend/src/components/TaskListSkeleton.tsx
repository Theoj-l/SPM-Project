import { Skeleton } from "@/components/ui/skeleton";

export default function TaskListSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, index) => (
        <div
          key={index}
          className="flex items-center gap-3 p-3 border border-gray-200 rounded-md"
        >
          {/* Checkbox */}
          <Skeleton className="h-5 w-5 rounded" />

          {/* Task Content */}
          <div className="flex-1 min-w-0">
            <Skeleton className="h-4 w-3/4 mb-2" />
            <Skeleton className="h-3 w-1/2" />
          </div>

          {/* Task Meta */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Status */}
            <Skeleton className="h-6 w-16 rounded-full" />

            {/* Assignees */}
            <div className="flex items-center gap-1">
              <Skeleton className="h-3 w-3 rounded-full" />
              <Skeleton className="h-3 w-12" />
            </div>

            {/* Due Date */}
            <Skeleton className="h-3 w-16" />

            {/* Actions */}
            <Skeleton className="h-4 w-4" />
          </div>
        </div>
      ))}
    </div>
  );
}
