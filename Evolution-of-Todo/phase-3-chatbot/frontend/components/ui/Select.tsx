/**
 * Select component for form inputs.
 * A styled wrapper around the native select element.
 */

import type { ComponentPropsWithoutRef } from "react";

type SelectProps = {
  /** Additional CSS classes to apply */
  className?: string;
} & ComponentPropsWithoutRef<"select">;

export default function Select({ className = "", ...props }: SelectProps) {
  const baseClasses =
    "block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100 disabled:cursor-not-allowed";

  const combinedClassName = `${baseClasses} ${className}`.trim();

  return <select className={combinedClassName} {...props} />;
}