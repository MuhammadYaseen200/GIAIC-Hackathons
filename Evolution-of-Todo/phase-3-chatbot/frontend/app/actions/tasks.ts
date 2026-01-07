"use server";

/**
 * Server Actions for task CRUD operations.
 *
 * Security:
 * - JWT token extracted from httpOnly cookie
 * - All requests authenticated via Bearer token
 * - Multi-tenancy enforced by backend
 *
 * State Management:
 * - Uses revalidatePath for cache invalidation
 * - Returns success/error states for UI feedback
 */

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import type { Task, FormState } from "@/types";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const COOKIE_NAME = "auth-token";

/**
 * Get the authentication token from cookies.
 */
async function getAuthToken(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get(COOKIE_NAME)?.value ?? null;
}

/**
 * Fetch tasks for the current user.
 *
 * @returns Array of tasks or empty array on error.
 */
export async function getTasks(): Promise<Task[]> {
  const token = await getAuthToken();

  if (!token) {
    console.error("getTasks: No auth token found");
    return [];
  }

  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/tasks`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      console.error("getTasks: Backend error", response.status);
      return [];
    }

    const data = await response.json();
    return data.data ?? [];
  } catch (error) {
    console.error("getTasks: Network error", error);
    return [];
  }
}

/**
 * Create a new task.
 *
 * @param prevState - Previous form state
 * @param formData - Form data with title and optional description
 * @returns Form state with success/error message
 */
export async function createTask(
  prevState: FormState | null,
  formData: FormData
): Promise<FormState> {
  const token = await getAuthToken();

  if (!token) {
    return {
      success: false,
      message: "You must be logged in to create tasks",
    };
  }

  const title = formData.get("title") as string;
  const description = (formData.get("description") as string) || "";
  const priority = formData.get("priority") as "high" | "medium" | "low" || "medium";
  const tagsInput = formData.get("tags") as string || "";
  const tags = tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);

  // Client-side validation
  if (!title || title.trim().length === 0) {
    return {
      success: false,
      message: "Title is required",
      errors: { title: ["Title cannot be empty"] },
    };
  }

  if (title.length > 200) {
    return {
      success: false,
      message: "Title too long",
      errors: { title: ["Title must be 200 characters or less"] },
    };
  }

  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/tasks`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: title.trim(),
        description: description.trim(),
        priority,
        tags
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        success: false,
        message: data.error?.message || "Failed to create task",
      };
    }

    // Revalidate dashboard to show new task
    revalidatePath("/dashboard");

    return {
      success: true,
      message: "Task created successfully",
    };
  } catch (error) {
    console.error("createTask: Error", error);
    return {
      success: false,
      message: "Unable to connect to server. Please try again.",
    };
  }
}

/**
 * Toggle task completion status.
 *
 * @param taskId - UUID of the task to toggle
 * @returns Form state with success/error message
 */
export async function toggleTaskComplete(taskId: string): Promise<FormState> {
  const token = await getAuthToken();

  if (!token) {
    return {
      success: false,
      message: "You must be logged in",
    };
  }

  try {
    const response = await fetch(
      `${BACKEND_URL}/api/v1/tasks/${taskId}/complete`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      const data = await response.json();
      return {
        success: false,
        message: data.error?.message || "Failed to update task",
      };
    }

    revalidatePath("/dashboard");

    return {
      success: true,
      message: "Task updated",
    };
  } catch (error) {
    console.error("toggleTaskComplete: Error", error);
    return {
      success: false,
      message: "Unable to connect to server",
    };
  }
}

/**
 * Delete a task.
 *
 * @param taskId - UUID of the task to delete
 * @returns Form state with success/error message
 */
export async function deleteTask(taskId: string): Promise<FormState> {
  const token = await getAuthToken();

  if (!token) {
    return {
      success: false,
      message: "You must be logged in",
    };
  }

  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/tasks/${taskId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const data = await response.json();
      return {
        success: false,
        message: data.error?.message || "Failed to delete task",
      };
    }

    revalidatePath("/dashboard");

    return {
      success: true,
      message: "Task deleted",
    };
  } catch (error) {
    console.error("deleteTask: Error", error);
    return {
      success: false,
      message: "Unable to connect to server",
    };
  }
}

/**
 * Update a task's title and/or description.
 *
 * @param taskId - UUID of the task to update
 * @param prevState - Previous form state
 * @param formData - Form data with title and/or description
 * @returns Form state with success/error message
 */
export async function updateTask(
  taskId: string,
  prevState: FormState | null,
  formData: FormData
): Promise<FormState> {
  const token = await getAuthToken();

  if (!token) {
    return {
      success: false,
      message: "You must be logged in",
    };
  }

  const title = formData.get("title") as string | null;
  const description = formData.get("description") as string | null;
  const priority = formData.get("priority") as "high" | "medium" | "low" | null;
  const tagsInput = formData.get("tags") as string | null;
  const tags = tagsInput ? tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0) : null;

  const updateData: Record<string, any> = {};
  if (title !== null) updateData.title = title.trim();
  if (description !== null) updateData.description = description.trim();
  if (priority !== null) updateData.priority = priority;
  if (tags !== null) updateData.tags = tags;

  if (Object.keys(updateData).length === 0) {
    return {
      success: false,
      message: "No changes to save",
    };
  }

  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/tasks/${taskId}`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updateData),
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        success: false,
        message: data.error?.message || "Failed to update task",
      };
    }

    revalidatePath("/dashboard");

    return {
      success: true,
      message: "Task updated successfully",
    };
  } catch (error) {
    console.error("updateTask: Error", error);
    return {
      success: false,
      message: "Unable to connect to server",
    };
  }
}
