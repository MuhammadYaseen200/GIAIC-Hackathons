'use client';

import { useState, useEffect } from 'react';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import type { Task } from '@/types';

interface TaskToolbarProps {
  tasks: Task[];
  onFilteredTasksChange: (filteredTasks: Task[]) => void;
}

export default function TaskToolbar({ tasks, onFilteredTasksChange }: TaskToolbarProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');

  useEffect(() => {
    // Apply filters whenever any filter value changes
    let filtered = [...tasks];

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(task =>
        task.title.toLowerCase().includes(term) ||
        task.description.toLowerCase().includes(term) ||
        task.tags.some(tag => tag.toLowerCase().includes(term))
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(task => {
        if (statusFilter === 'completed') return task.completed;
        if (statusFilter === 'pending') return !task.completed;
        return true;
      });
    }

    // Apply priority filter
    if (priorityFilter !== 'all') {
      filtered = filtered.filter(task => task.priority === priorityFilter);
    }

    onFilteredTasksChange(filtered);
  }, [searchTerm, statusFilter, priorityFilter, tasks, onFilteredTasksChange]);

  return (
    <div className="mb-6 p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Search Input */}
        <div className="md:col-span-2">
          <Input
            type="text"
            placeholder="Search tasks..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full"
          />
        </div>

        {/* Status Filter */}
        <div>
          <Select
            name="status-filter"
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full"
          >
            <option value="all">All Tasks</option>
            <option value="pending">Pending</option>
            <option value="completed">Completed</option>
          </Select>
        </div>

        {/* Priority Filter */}
        <div>
          <Select
            name="priority-filter"
            id="priority-filter"
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="w-full"
          >
            <option value="all">All Priorities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </Select>
        </div>
      </div>
    </div>
  );
}