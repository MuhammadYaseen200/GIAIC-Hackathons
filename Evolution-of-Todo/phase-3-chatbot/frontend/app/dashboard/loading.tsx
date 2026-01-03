/**
 * Dashboard loading state.
 * Displayed while the dashboard page is loading (data fetching, etc.).
 *
 * Next.js automatically uses this component as a loading UI
 * when navigation occurs to /dashboard.
 *
 * Accessibility:
 * - role="status" indicates loading state to assistive technologies
 * - Screen reader announcement of loading completion
 */

import { TaskListSkeleton, FormSkeleton } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <div>
      {/* Page Header */}
      <div className="mb-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 bg-gray-200 rounded" />
          <div className="h-4 w-72 bg-gray-200 rounded" />
        </div>
      </div>

      {/* Task Form Skeleton */}
      <div className="mb-6">
        <FormSkeleton />
      </div>

      {/* Task List Skeleton */}
      <TaskListSkeleton count={5} />

      {/* Screen Reader Announcement */}
      <span className="sr-only" role="status" aria-live="polite">
        Loading dashboard content...
      </span>
    </div>
  );
}
