"use server";

/**
 * Server Actions for authentication operations.
 *
 * Security:
 * - JWT tokens stored in httpOnly cookies (cannot be accessed by client JS)
 * - Cookie settings follow ADR-004
 * - All backend calls use secure fetch
 *
 * State Management:
 * - Uses Next.js form state pattern with useFormState
 * - Returns success/error states for UI feedback
 */

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { FormState } from "@/types";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const COOKIE_NAME = "auth-token";

/**
 * Cookie options following ADR-004 specification.
 * - httpOnly: true - Cannot be accessed by client-side JavaScript
 * - secure: production only - Requires HTTPS in production
 * - sameSite: lax - Provides CSRF protection while allowing normal navigation
 * - path: / - Cookie available to entire app
 * - maxAge: 24 hours - Token expires after 1 day
 */
const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
  maxAge: 86400, // 24 hours in seconds
};

/**
 * Register a new user account.
 *
 * @param prevState - Previous form state (unused, required by useFormState)
 * @param formData - Form data containing email and password
 * @returns Form state with success/error message
 */
export async function register(
  prevState: FormState | null,
  formData: FormData
): Promise<FormState> {
  // Extract form fields
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;

  // Client-side validation (defense in depth)
  const errors: Record<string, string[]> = {};

  if (!email || !email.includes("@")) {
    errors.email = ["Please enter a valid email address"];
  }

  if (!password || password.length < 8) {
    errors.password = ["Password must be at least 8 characters"];
  }

  if (Object.keys(errors).length > 0) {
    return {
      success: false,
      message: "Please fix the errors below",
      errors,
    };
  }

  try {
    // Call backend registration endpoint
    const response = await fetch(`${BACKEND_URL}/api/v1/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      // Backend returned an error
      return {
        success: false,
        message: data.error?.message || "Registration failed",
        errors: data.error?.details,
      };
    }

    // Registration successful
    return {
      success: true,
      message: "Account created successfully! Please sign in.",
    };
  } catch (error) {
    // Network or unexpected error
    console.error("Registration error:", error);
    return {
      success: false,
      message: "Unable to connect to the server. Please try again.",
    };
  }
}

/**
 * Log in an existing user.
 *
 * @param prevState - Previous form state (unused, required by useFormState)
 * @param formData - Form data containing email and password
 * @returns Form state with success/error message
 *
 * Side Effects:
 * - Sets httpOnly cookie with JWT token on success
 * - Redirects to /dashboard on success
 */
export async function login(
  prevState: FormState | null,
  formData: FormData
): Promise<FormState> {
  // Extract form fields
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;

  // Client-side validation
  const errors: Record<string, string[]> = {};

  if (!email) {
    errors.email = ["Email is required"];
  }

  if (!password) {
    errors.password = ["Password is required"];
  }

  if (Object.keys(errors).length > 0) {
    return {
      success: false,
      message: "Please fill in all fields",
      errors,
    };
  }

  try {
    // Call backend login endpoint
    const response = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      // Backend returned an error
      return {
        success: false,
        message: data.error?.message || "Login failed",
        errors: data.error?.details,
      };
    }

    // Extract JWT token from response
    const token = data.data?.token;

    if (!token) {
      return {
        success: false,
        message: "Invalid response from server",
      };
    }

    // Set httpOnly cookie with JWT token
    const cookieStore = await cookies();
    cookieStore.set(COOKIE_NAME, token, COOKIE_OPTIONS);

    // Redirect to dashboard
    // Note: This redirect will throw an error (expected Next.js behavior)
    redirect("/dashboard");
  } catch (error) {
    // Check if error is from redirect (expected behavior)
    if (error instanceof Error && error.message === "NEXT_REDIRECT") {
      // Re-throw to allow redirect to proceed
      throw error;
    }

    // Network or unexpected error
    console.error("Login error:", error);
    return {
      success: false,
      message: "Unable to connect to the server. Please try again.",
    };
  }
}

/**
 * Log out the current user.
 *
 * Side Effects:
 * - Deletes the auth-token httpOnly cookie
 * - Redirects to /login
 */
export async function logout(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(COOKIE_NAME);
  redirect("/login");
}
