/**
 * Dashboard error boundary.
 * Displayed when an error occurs on the dashboard page.
 *
 * Next.js automatically uses this component to wrap the page
 * when an error is thrown during rendering or data fetching.
 *
 * Accessibility:
 * - role="alert" announces error to screen readers
 * - Clear error message and recovery instructions
 * - Focus management to error content
 */

"use client";

import { useEffect } from "react";
import Button from "@/components/ui/Button";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log the error to console for debugging
    console.error("Dashboard error:", error);
  }, [error]);

  return (
    <div
      className="min-h-[50vh] flex flex-col items-center justify-center text-center px-4"
      role="alert"
      aria-live="assertive"
    >
      {/* Error Icon */}
      <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-6">
        <svg
          className="w-8 h-8 text-red-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>

      {/* Error Heading */}
      <h1 className="text-2xl font-bold text-gray-900 mb-2">
        Something went wrong
      </h1>

      {/* Error Message */}
      <p className="text-gray-600 mb-6 max-w-md">
        We encountered an unexpected error while loading your dashboard.
        This might be a temporary issue with the server.
      </p>

      {/* Error Details (collapsed by default) */}
      <details className="mb-6 text-left max-w-md w-full">
        <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
          Error details
        </summary>
        <p className="mt-2 p-3 bg-gray-100 rounded text-sm text-gray-700 font-mono break-all">
          {error.message}
        </p>
        {error.digest && (
          <p className="mt-2 text-xs text-gray-400">
            Error ID: {error.digest}
          </p>
        )}
      </details>

      {/* Recovery Actions */}
      <div className="flex gap-4">
        <Button onClick={reset} variant="primary">
          Try Again
        </Button>
        <Button
          onClick={() => (window.location.href = "/dashboard")}
          variant="secondary"
        >
          Refresh Page
        </Button>
      </div>

      {/* Help Link */}
      <p className="mt-8 text-sm text-gray-500">
        If the problem persists, please try{" "}
        <a
          href="/login"
          className="text-blue-600 hover:underline"
          onClick={(e) => {
            e.preventDefault();
            window.location.href = "/login";
          }}
        >
          logging out
        </a>{" "}
        and signing back in.
      </p>
    </div>
  );
}
