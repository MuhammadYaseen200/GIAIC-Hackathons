"use client";

/**
 * TaskForm component for creating new tasks.
 * Uses React 19 useActionState for form state management.
 */

import { useActionState, useRef, useEffect } from "react";
import { createTask } from "@/app/actions/tasks";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { toast } from "sonner";
import type { FormState } from "@/types";

const initialState: FormState = {
  success: false,
  message: "",
};

export function TaskForm() {
  const [state, formAction, isPending] = useActionState(createTask, initialState);
  const formRef = useRef<HTMLFormElement>(null);

  // Reset form and show toast on successful submission
  useEffect(() => {
    if (state.success) {
      formRef.current?.reset();
      toast.success("Task created successfully");
    } else if (state.success === false && state.message) {
      toast.error(state.message);
    }
  }, [state]);

  return (
    <Card variant="elevated" className="mb-6">
      <CardHeader>
        <CardTitle>Add New Task</CardTitle>
      </CardHeader>
      <CardContent>
        <form ref={formRef} action={formAction} className="space-y-4">
          {/* Error/Success Message - also shown for accessibility */}
          {state.message && !state.success && (
            <div
              className="p-3 rounded-md text-sm bg-red-50 text-red-700 border border-red-200"
              role="alert"
            >
              {state.message}
            </div>
          )}

          {/* Title Input */}
          <div>
            <Input
              name="title"
              type="text"
              placeholder="What needs to be done?"
              required
              maxLength={200}
              disabled={isPending}
              error={state.errors?.title?.[0]}
              aria-describedby={state.errors?.title ? "title-error" : undefined}
            />
            {state.errors?.title && (
              <p id="title-error" className="mt-1 text-sm text-red-600">
                {state.errors.title[0]}
              </p>
            )}
          </div>

          {/* Description Input (optional) */}
          <div>
            <textarea
              name="description"
              placeholder="Add a description (optional)"
              maxLength={1000}
              disabled={isPending}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed resize-none"
            />
          </div>

          {/* Priority Selection */}
          <div>
            <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-1">
              Priority
            </label>
            <Select
              name="priority"
              id="priority"
              defaultValue="medium"
              disabled={isPending}
              className="w-full"
            >
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </Select>
          </div>

          {/* Tags Input */}
          <div>
            <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-1">
              Tags (comma-separated)
            </label>
            <Input
              name="tags"
              type="text"
              placeholder="e.g., work, urgent, personal"
              disabled={isPending}
              maxLength={200}
            />
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={isPending}
            className="w-full"
          >
            {isPending ? "Adding..." : "Add Task"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
