/**
 * TypeScript type definitions for the Todo application.
 * Matches backend SQLModel schemas and API contracts from spec.md.
 */

// =============================================================================
// User Types
// =============================================================================

/**
 * Represents an authenticated user.
 */
export interface User {
  id: string; // UUID
  email: string;
  created_at: string; // ISO 8601
}

/**
 * Request payload for user registration.
 */
export interface RegisterRequest {
  email: string; // Required, valid email format
  password: string; // Required, min 8 chars
}

/**
 * Request payload for user login.
 */
export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * Response payload for successful authentication.
 */
export interface AuthResponse {
  success: true;
  data: {
    user: User;
    token: string; // JWT
    expires_at: string; // ISO 8601
  };
}

// =============================================================================
// Task Types
// =============================================================================

/**
 * Represents a todo task.
 */
export interface Task {
  id: string; // UUID
  user_id: string; // UUID
  title: string; // 1-200 chars
  description: string; // 0-1000 chars
  completed: boolean;
  priority: "high" | "medium" | "low"; // Task priority level
  tags: string[]; // Array of tag strings
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}

/**
 * Request payload for creating a task.
 */
export interface TaskCreateRequest {
  title: string; // Required
  description?: string; // Optional
  priority?: "high" | "medium" | "low"; // Optional priority
  tags?: string[]; // Optional tags array
}

/**
 * Request payload for updating a task.
 */
export interface TaskUpdateRequest {
  title?: string; // Optional, but at least one field required
  description?: string; // Optional
  priority?: "high" | "medium" | "low"; // Optional priority
  tags?: string[]; // Optional tags array
}

/**
 * Response payload for task list.
 */
export interface TaskListResponse {
  success: true;
  data: Task[];
  meta: {
    total: number;
    limit: number;
    offset: number;
  };
}

/**
 * Response payload for single task.
 */
export interface TaskResponse {
  success: true;
  data: Task;
}

/**
 * Response payload for task deletion.
 */
export interface DeleteResponse {
  success: true;
  data: {
    id: string;
    deleted: true;
  };
}

// =============================================================================
// Error Types
// =============================================================================

/**
 * Standard error response from the API.
 */
export interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, string>;
  };
}

/**
 * Union type for all API responses.
 */
export type ApiResponse<T> =
  | { success: true; data: T }
  | ErrorResponse;

// =============================================================================
// Form State Types
// =============================================================================

/**
 * State for form submissions with Server Actions.
 */
export interface FormState {
  success: boolean;
  message: string;
  errors?: Record<string, string[]>;
}

/**
 * Initial form state for useFormState hook.
 */
export const initialFormState: FormState = {
  success: false,
  message: "",
};
