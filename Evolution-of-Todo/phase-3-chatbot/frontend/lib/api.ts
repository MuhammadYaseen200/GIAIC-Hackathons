/**
 * API client for communicating with the FastAPI backend.
 *
 * Uses Next.js API proxy (configured in next.config.ts) to avoid CORS issues.
 * All requests go to /api/* which is rewritten to the backend URL.
 */

import type { ApiResponse, ErrorResponse } from "@/types";

// Defensive: trim and validate the API URL to prevent malformed env vars
const rawApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim().split(' ')[0] || '';
const API_BASE = rawApiUrl
  ? `${rawApiUrl}/api/v1`
  : "/api/v1";

/**
 * Custom error class for API errors.
 */
export class ApiError extends Error {
  code: string;
  status: number;
  details?: Record<string, string>;

  constructor(
    message: string,
    code: string,
    status: number,
    details?: Record<string, string>
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

/**
 * Options for API requests.
 */
interface FetchOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
}

/**
 * Make an authenticated API request.
 *
 * @param endpoint - API endpoint (without /api/v1 prefix)
 * @param options - Fetch options
 * @returns Parsed JSON response
 * @throws ApiError on failure
 */
export async function apiFetch<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const { body, headers: customHeaders, ...restOptions } = options;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...customHeaders,
  };

  const config: RequestInit = {
    ...restOptions,
    headers,
  };

  if (body !== undefined) {
    config.body = JSON.stringify(body);
  }

  const url = `${API_BASE}${endpoint}`;

  try {
    const response = await fetch(url, config);

    // Handle empty responses (e.g., 204 No Content)
    if (response.status === 204) {
      return {} as T;
    }

    const data = await response.json();

    if (!response.ok) {
      const errorResponse = data as ErrorResponse;
      throw new ApiError(
        errorResponse.error?.message || "Request failed",
        errorResponse.error?.code || "UNKNOWN_ERROR",
        response.status,
        errorResponse.error?.details
      );
    }

    return data as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    // Network or parsing error
    throw new ApiError(
      error instanceof Error ? error.message : "Network error",
      "NETWORK_ERROR",
      0
    );
  }
}

// =============================================================================
// Convenience methods
// =============================================================================

/**
 * GET request.
 */
export async function apiGet<T>(endpoint: string): Promise<T> {
  return apiFetch<T>(endpoint, { method: "GET" });
}

/**
 * POST request.
 */
export async function apiPost<T>(endpoint: string, body?: unknown): Promise<T> {
  return apiFetch<T>(endpoint, { method: "POST", body });
}

/**
 * PUT request.
 */
export async function apiPut<T>(endpoint: string, body?: unknown): Promise<T> {
  return apiFetch<T>(endpoint, { method: "PUT", body });
}

/**
 * PATCH request.
 */
export async function apiPatch<T>(endpoint: string, body?: unknown): Promise<T> {
  return apiFetch<T>(endpoint, { method: "PATCH", body });
}

/**
 * DELETE request.
 */
export async function apiDelete<T>(endpoint: string): Promise<T> {
  return apiFetch<T>(endpoint, { method: "DELETE" });
}

// =============================================================================
// Response helpers
// =============================================================================

/**
 * Check if a response is an error response.
 */
export function isErrorResponse(response: unknown): response is ErrorResponse {
  return (
    typeof response === "object" &&
    response !== null &&
    "success" in response &&
    (response as { success: boolean }).success === false
  );
}

/**
 * Extract data from a successful API response.
 */
export function extractData<T>(response: ApiResponse<T>): T {
  if (response.success) {
    return response.data;
  }
  throw new ApiError(
    response.error.message,
    response.error.code,
    400,
    response.error.details
  );
}
