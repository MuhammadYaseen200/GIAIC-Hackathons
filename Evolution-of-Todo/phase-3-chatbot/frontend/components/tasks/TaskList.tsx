/**
 * TaskList component for displaying a list of tasks.
 * Handles empty state and task rendering.
 */

import { TaskItem } from "./TaskItem";
import type { Task } from "@/types";

interface TaskListProps {
  tasks: Task[];
  filteredTasks?: Task[]; // Optional prop for filtered tasks
}

export function TaskList({ tasks, filteredTasks }: TaskListProps) {
  // Use filtered tasks if provided, otherwise use all tasks
  const displayTasks = filteredTasks !== undefined ? filteredTasks : tasks;

  if (displayTasks.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
          <svg
            className="w-8 h-8 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-1">No tasks found</h3>
        <p className="text-gray-500">
          {tasks.length === 0
            ? "Add your first task using the form above."
            : "Try adjusting your search or filter criteria."}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          Your Tasks ({displayTasks.length})
        </h2>
        <div className="text-sm text-gray-500">
          {displayTasks.filter((t) => t.completed).length} completed
        </div>
      </div>

      {displayTasks.map((task) => (
        <TaskItem key={task.id} task={task} />
      ))}
    </div>
  );
}
