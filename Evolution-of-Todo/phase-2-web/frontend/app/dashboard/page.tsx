/**
 * Dashboard page - main task management view.
 * Displays task creation form and list of tasks.
 */

import { getTasks } from "@/app/actions/tasks";
import { TaskForm } from "@/components/tasks/TaskForm";
import { TaskList } from "@/components/tasks/TaskList";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const tasks = await getTasks();

  return (
    <div>
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-gray-600">
          Manage your tasks and stay organized.
        </p>
      </div>

      {/* Task Creation Form */}
      <TaskForm />

      {/* Task List */}
      <TaskList tasks={tasks} />
    </div>
  );
}
