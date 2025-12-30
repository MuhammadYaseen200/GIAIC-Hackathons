"use client";

/**
 * Toast notification component using sonner.
 *
 * Provides accessible toast notifications for:
 * - Success feedback after operations
 * - Error messages for failed operations
 * - Loading state indicators
 *
 * Accessibility:
 * - Uses sonner's built-in accessibility features
 * - Screen reader announcements via aria-live regions
 * - Keyboard dismiss support
 */

import { Toaster, toast } from "sonner";

/**
 * Toast provider component.
 * Must be rendered once at the root level to enable toast notifications.
 *
 * Usage: Place <ToastProvider /> in the root layout or dashboard layout.
 */
export function ToastProvider() {
  return (
    <Toaster
      position="top-right"
      richColors
      closeButton
      expand
      duration={4000}
      toastOptions={{
        className: "shadow-lg",
      }}
    />
  );
}

/**
 * Success toast notification.
 * Use for successful operations like task creation, deletion, etc.
 *
 * @param message - The success message to display
 * @param description - Optional additional description
 */
export function showSuccess(message: string, description?: string) {
  toast.success(message, {
    description,
    duration: 3000,
  });
}

/**
 * Error toast notification.
 * Use for failed operations and error states.
 *
 * @param message - The error message to display
 * @param description - Optional additional details
 */
export function showError(message: string, description?: string) {
  toast.error(message, {
    description,
    duration: 5000,
  });
}

/**
 * Info toast notification.
 * Use for informational messages.
 *
 * @param message - The info message to display
 * @param description - Optional additional details
 */
export function showInfo(message: string, description?: string) {
  toast.info(message, {
    description,
    duration: 4000,
  });
}

/**
 * Warning toast notification.
 * Use for cautionary messages.
 *
 * @param message - The warning message to display
 * @param description - Optional additional details
 */
export function showWarning(message: string, description?: string) {
  toast.warning(message, {
    description,
    duration: 4000,
  });
}

/**
 * Loading toast notification.
 * Use to indicate an ongoing operation.
 *
 * @param message - The loading message
 * @returns A dismiss function to resolve the loading toast
 */
export function showLoading(message: string) {
  return toast.loading(message);
}

/**
 * Promise toast notification.
 * Automatically shows loading, success, or error states based on promise resolution.
 *
 * @param promise - The promise to track
 * @param messages - Object with loading, success, and error messages
 */
export function showPromise<T>(
  promise: Promise<T>,
  messages: {
    loading: string;
    success: string;
    error: string;
  }
) {
  toast.promise(promise, {
    loading: messages.loading,
    success: messages.success,
    error: messages.error,
  });
}

export { Toaster, toast };
