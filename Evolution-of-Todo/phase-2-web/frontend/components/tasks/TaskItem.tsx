"use client";

/**
 * TaskItem component for displaying and interacting with a single task.
 * Supports toggle completion and delete actions with confirmation dialog.
 */

import { useState, useTransition } from "react";
import { toggleTaskComplete, deleteTask } from "@/app/actions/tasks";
import { Card, CardContent } from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import type { Task } from "@/types";
import { showSuccess, showError } from "@/components/ui/Toast";

interface TaskItemProps {
  task: Task;
}

export function TaskItem({ task }: TaskItemProps) {
  const [isPending, startTransition] = useTransition();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const handleToggle = () => {
    startTransition(async () => {
      const result = await toggleTaskComplete(task.id);
      if (result.success) {
        showSuccess(
          task.completed ? "Task marked as incomplete" : "Task completed",
          task.title
        );
      } else {
        showError("Failed to update task", result.message);
      }
    });
  };

  const handleDelete = () => {
    startTransition(async () => {
      const result = await deleteTask(task.id);
      if (result.success) {
        showSuccess("Task deleted", task.title);
        setShowDeleteDialog(false);
      } else {
        showError("Failed to delete task", result.message);
      }
    });
  };

  return (
    <>
      <Card
        className={`transition-all duration-200 ${
          task.completed ? "opacity-60" : ""
        } ${isPending ? "pointer-events-none" : ""}`}
      >
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            {/* Checkbox */}
            <button
              type="button"
              onClick={handleToggle}
              disabled={isPending}
              className={`mt-0.5 w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                task.completed
                  ? "bg-green-500 border-green-500 text-white"
                  : "border-gray-300 hover:border-green-400"
              } ${isPending ? "opacity-50" : ""}`}
              aria-label={
                task.completed ? "Mark as incomplete" : "Mark as complete"
              }
            >
              {task.completed && (
                <svg
                  className="w-3 h-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={3}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              )}
            </button>

            {/* Task Content */}
            <div className="flex-1 min-w-0">
              <h3
                className={`font-medium text-gray-900 ${
                  task.completed ? "line-through text-gray-500" : ""
                }`}
              >
                {task.title}
              </h3>
              {task.description && (
                <p
                  className={`mt-1 text-sm ${
                    task.completed ? "text-gray-400" : "text-gray-600"
                  }`}
                >
                  {task.description}
                </p>
              )}
              <p className="mt-2 text-xs text-gray-400">
                {new Date(task.created_at).toLocaleDateString()}
              </p>
            </div>

            {/* Delete Button */}
            <Button
              variant="danger"
              size="sm"
              onClick={() => setShowDeleteDialog(true)}
              disabled={isPending}
              aria-label="Delete task"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      {showDeleteDialog && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-dialog-title"
          aria-describedby="delete-dialog-description"
        >
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-red-600"
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
              <div>
                <h2
                  id="delete-dialog-title"
                  className="text-lg font-semibold text-gray-900"
                >
                  Delete Task?
                </h2>
                <p
                  id="delete-dialog-description"
                  className="text-sm text-gray-500"
                >
                  This action cannot be undone.
                </p>
              </div>
            </div>

            <p className="text-gray-700 mb-6">
              Are you sure you want to delete <strong>"{task.title}"</strong>?
            </p>

            <div className="flex gap-3 justify-end">
              <Button
                variant="secondary"
                onClick={() => setShowDeleteDialog(false)}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={handleDelete}
                loading={isPending}
              >
                Delete Task
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
