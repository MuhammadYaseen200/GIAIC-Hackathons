import Link from "next/link";
import LoginForm from "@/components/auth/LoginForm";

/**
 * Login page.
 *
 * Layout:
 * - Centered card with login form
 * - Link to register page for new users
 * - Simple, focused design
 *
 * Accessibility:
 * - Proper heading hierarchy (h1)
 * - Descriptive link text
 * - Responsive on mobile devices
 */

export const metadata = {
  title: "Sign In | Todo App",
  description: "Sign in to your account to manage your tasks",
};

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md">
        {/* Card container */}
        <div className="bg-white shadow-md rounded-lg p-6 sm:p-8">
          {/* Header */}
          <div className="mb-6 text-center">
            <h1 className="text-2xl font-bold text-gray-900">
              Sign In
            </h1>
            <p className="mt-2 text-sm text-gray-600">
              Welcome back! Please sign in to continue
            </p>
          </div>

          {/* Login form */}
          <LoginForm />

          {/* Link to register */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Don&apos;t have an account?{" "}
              <Link
                href="/register"
                className="font-medium text-blue-600 hover:text-blue-500 focus:outline-none focus:underline"
              >
                Create account
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
