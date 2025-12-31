"use client";

/**
 * Login form component.
 *
 * Uses Next.js Server Actions with useActionState for progressive enhancement.
 * On successful login, server action sets httpOnly cookie and redirects to dashboard.
 *
 * Accessibility:
 * - Proper form semantics
 * - Error messages associated with inputs
 * - Loading state prevents double submission
 * - Keyboard navigation support
 */

import { useActionState } from "react";
import { login } from "@/app/actions/auth";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import type { FormState } from "@/types";

const initialState: FormState = {
  success: false,
  message: "",
};

export default function LoginForm() {
  // useActionState returns [state, formAction, isPending]
  // isPending tracks the form submission state, replacing the need for useFormStatus
  const [state, formAction, isPending] = useActionState(login, initialState);

  return (
    <form action={formAction} className="space-y-4">
      {/* Error message */}
      {!state.success && state.message && (
        <div
          className="p-4 bg-red-50 border border-red-200 rounded text-red-800"
          role="alert"
        >
          {state.message}
        </div>
      )}

      {/* Email input */}
      <Input
        type="email"
        name="email"
        label="Email"
        placeholder="you@example.com"
        required
        autoComplete="email"
        error={state.errors?.email?.[0]}
      />

      {/* Password input */}
      <Input
        type="password"
        name="password"
        label="Password"
        placeholder="Enter your password"
        required
        autoComplete="current-password"
        error={state.errors?.password?.[0]}
      />

      {/* Submit button - isPending from useActionState tracks loading state */}
      <Button type="submit" variant="primary" size="md" loading={isPending} className="w-full">
        {isPending ? "Signing in..." : "Sign In"}
      </Button>
    </form>
  );
}
