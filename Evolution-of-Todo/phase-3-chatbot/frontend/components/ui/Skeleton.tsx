/**
 * Skeleton loader component for displaying loading states.
 * Used for TaskList while tasks are being fetched.
 *
 * Accessibility:
 * - role="status" indicates to screen readers that content is loading
 * - aria-label provides context about what's being loaded
 */

interface SkeletonProps {
  className?: string;
  variant?: "text" | "rectangular" | "circular";
}

export function Skeleton({ className = "", variant = "rectangular" }: SkeletonProps) {
  const variantStyles = {
    text: "h-4 rounded",
    rectangular: "rounded-md",
    circular: "rounded-full",
  };

  return (
    <div
      className={`animate-pulse bg-gray-200 ${variantStyles[variant]} ${className}`}
      role="status"
      aria-label="Loading content..."
    />
  );
}

/**
 * Task card skeleton loader.
 * Displays a placeholder while task list is loading.
 */
export function TaskCardSkeleton() {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-start gap-3">
        {/* Checkbox skeleton */}
        <Skeleton variant="circular" className="w-5 h-5 mt-0.5" />

        {/* Task content skeleton */}
        <div className="flex-1 min-w-0 space-y-2">
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-3 w-24 mt-3" />
        </div>

        {/* Delete button skeleton */}
        <Skeleton variant="circular" className="w-8 h-8" />
      </div>
    </div>
  );
}

/**
 * Task list skeleton loader.
 * Displays multiple task card skeletons to indicate loading state.
 */
export function TaskListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3" aria-hidden="true">
      {/* Header skeleton */}
      <div className="flex items-center justify-between mb-4">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-4 w-20" />
      </div>

      {/* Task card skeletons */}
      {Array.from({ length: count }).map((_, index) => (
        <TaskCardSkeleton key={index} />
      ))}

      {/* Screen reader announcement */}
      <span className="sr-only">Loading tasks...</span>
    </div>
  );
}

/**
 * Form skeleton loader.
 * Displays a placeholder for forms while loading.
 */
export function FormSkeleton() {
  return (
    <div className="space-y-4" aria-hidden="true">
      <Skeleton className="h-6 w-40" />
      <div className="space-y-2">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    </div>
  );
}
