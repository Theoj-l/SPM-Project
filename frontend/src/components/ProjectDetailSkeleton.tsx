import { Skeleton } from "@/components/ui/skeleton";

export default function ProjectDetailSkeleton() {
  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded-md" />
          <div>
            <Skeleton className="h-8 w-48 mb-2" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <Skeleton className="h-8 w-20 rounded-full" />
      </div>

      {/* Tasks Section */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <Skeleton className="h-6 w-16" />
          <Skeleton className="h-8 w-24" />
        </div>

        <div className="p-4">
          <TaskListSkeleton />
        </div>
      </div>
    </div>
  );
}

function TaskListSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 3 }).map((_, index) => (
        <div
          key={index}
          className="flex items-center gap-3 p-3 border border-gray-200 rounded-md"
        >
          <Skeleton className="h-5 w-5 rounded" />
          <div className="flex-1 min-w-0">
            <Skeleton className="h-4 w-3/4 mb-2" />
            <Skeleton className="h-3 w-1/2" />
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <Skeleton className="h-6 w-16 rounded-full" />
            <div className="flex items-center gap-1">
              <Skeleton className="h-3 w-3 rounded-full" />
              <Skeleton className="h-3 w-12" />
            </div>
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-4 w-4" />
          </div>
        </div>
      ))}
    </div>
  );
}
