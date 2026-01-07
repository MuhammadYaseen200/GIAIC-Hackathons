/**
 * Dashboard page - main task management view.
 * Displays task creation form and list of tasks.
 */

import { getTasks } from "@/app/actions/tasks";
import TaskManager from "@/components/tasks/TaskManager";

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

      {/* Task Manager with forms, toolbar and list */}
      <TaskManager initialTasks={tasks} />
    </div>
  );
}
