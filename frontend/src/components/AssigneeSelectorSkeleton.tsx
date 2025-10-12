import { Skeleton } from "@/components/ui/skeleton";

export default function AssigneeSelectorSkeleton() {
  return (
    <div className="space-y-2">
      {/* Selected Assignees */}
      <div className="flex flex-wrap gap-2">
        {Array.from({ length: 2 }).map((_, index) => (
          <div
            key={index}
            className="flex items-center gap-2 bg-gray-100 rounded-full px-3 py-1"
          >
            <Skeleton className="h-4 w-4 rounded-full" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-4 rounded-full" />
          </div>
        ))}
      </div>

      {/* Search Input */}
      <div className="relative">
        <Skeleton className="h-10 w-full rounded-md" />
        <div className="absolute right-3 top-1/2 -translate-y-1/2">
          <Skeleton className="h-4 w-4" />
        </div>
      </div>

      {/* Dropdown */}
      <div className="border border-gray-200 rounded-md p-2 space-y-2">
        {Array.from({ length: 3 }).map((_, index) => (
          <div
            key={index}
            className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded"
          >
            <Skeleton className="h-8 w-8 rounded-full" />
            <div className="flex-1">
              <Skeleton className="h-4 w-24 mb-1" />
              <Skeleton className="h-3 w-32" />
            </div>
            <Skeleton className="h-4 w-4" />
          </div>
        ))}
      </div>
    </div>
  );
}
