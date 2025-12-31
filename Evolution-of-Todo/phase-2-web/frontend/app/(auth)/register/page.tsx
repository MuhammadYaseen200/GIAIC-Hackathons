import Link from "next/link";
import RegisterForm from "@/components/auth/RegisterForm";

/**
 * Registration page.
 *
 * Layout:
 * - Centered card with registration form
 * - Link to login page for existing users
 * - Simple, focused design
 *
 * Accessibility:
 * - Proper heading hierarchy (h1)
 * - Descriptive link text
 * - Responsive on mobile devices
 */

export const metadata = {
  title: "Create Account | Todo App",
  description: "Create a new account to start managing your tasks",
};

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md">
        {/* Card container */}
        <div className="bg-white shadow-md rounded-lg p-6 sm:p-8">
          {/* Header */}
          <div className="mb-6 text-center">
            <h1 className="text-2xl font-bold text-gray-900">
              Create Account
            </h1>
            <p className="mt-2 text-sm text-gray-600">
              Get started with your todo list
            </p>
          </div>

          {/* Registration form */}
          <RegisterForm />

          {/* Link to login */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{" "}
              <Link
                href="/login"
                className="font-medium text-blue-600 hover:text-blue-500 focus:outline-none focus:underline"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
