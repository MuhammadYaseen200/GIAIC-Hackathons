import type { Metadata } from "next";

/**
 * Layout for authentication pages (login, register).
 *
 * Features:
 * - Simple, minimal layout
 * - Optional branding area
 * - Centered content container
 * - Responsive design
 *
 * This layout is applied to all routes within the (auth) group.
 */

export const metadata: Metadata = {
  title: "Authentication",
  description: "Sign in or create an account",
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Optional: Add app branding/logo here */}
      <div className="absolute top-4 left-4">
        <h2 className="text-xl font-bold text-gray-800">Todo App</h2>
      </div>

      {/* Main content */}
      <main>{children}</main>
    </div>
  );
}
