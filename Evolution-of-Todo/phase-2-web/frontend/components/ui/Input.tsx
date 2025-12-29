import React from "react";

/**
 * Input component with label and error message support.
 *
 * Accessibility:
 * - Labels are properly associated with inputs via htmlFor/id
 * - Error messages have aria-describedby for screen readers
 * - aria-invalid attribute set when error is present
 * - Proper focus states for keyboard navigation
 */

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = "", id, type = "text", ...props }, ref) => {
    // Generate a unique ID if not provided (for label association)
    const inputId = id || React.useId();
    const errorId = error ? `${inputId}-error` : undefined;

    // Base styles
    const baseStyles =
      "block w-full px-4 py-2 border rounded transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1";

    // State styles
    const stateStyles = error
      ? "border-red-500 text-red-900 placeholder-red-300 focus:ring-red-500 focus:border-red-500"
      : "border-gray-300 focus:ring-blue-500 focus:border-blue-500";

    const combinedClassName = `${baseStyles} ${stateStyles} ${className}`;

    return (
      <div className="space-y-1">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-gray-700"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          type={type}
          className={combinedClassName}
          aria-invalid={error ? "true" : "false"}
          aria-describedby={errorId}
          {...props}
        />
        {error && (
          <p id={errorId} className="text-sm text-red-500" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export default Input;
