'use client';

import { useState, useEffect } from 'react';
import { TaskForm } from './TaskForm';
import { TaskList } from './TaskList';
import TaskToolbar from './TaskToolbar';
import type { Task } from '@/types';

interface TaskManagerProps {
  initialTasks: Task[];
}

export default function TaskManager({ initialTasks }: TaskManagerProps) {
  const [tasks, setTasks] = useState<Task[]>(initialTasks);
  const [filteredTasks, setFilteredTasks] = useState<Task[]>(initialTasks);

  // Update tasks when initialTasks changes (e.g., after adding/deleting tasks)
  useEffect(() => {
    setTasks(initialTasks);
    // Also update filtered tasks to ensure consistency
    setFilteredTasks(initialTasks);
  }, [initialTasks]);

  return (
    <div>
      {/* Task Creation Form */}
      <TaskForm />

      {/* Toolbar with Search and Filters */}
      <TaskToolbar tasks={tasks} onFilteredTasksChange={setFilteredTasks} />

      {/* Task List */}
      <TaskList tasks={tasks} filteredTasks={filteredTasks} />
    </div>
  );
}