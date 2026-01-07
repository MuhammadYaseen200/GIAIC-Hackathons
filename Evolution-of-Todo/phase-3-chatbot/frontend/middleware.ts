/**
 * Next.js Middleware for authentication and request handling.
 *
 * Implements ADR-004: HTTP-Only Cookie JWT Strategy
 * - Reads JWT from httpOnly cookie (auth-token)
 * - Adds Authorization header for API requests
 * - Redirects unauthenticated users from protected routes
 */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Cookie name for storing the JWT token.
 */
const AUTH_COOKIE_NAME = "auth-token";

/**
 * Routes that require authentication.
 */
const PROTECTED_ROUTES = ["/dashboard"];

/**
 * Routes that should redirect to dashboard if already authenticated.
 */
const AUTH_ROUTES = ["/login", "/register"];

/**
 * API routes that should have the Authorization header injected.
 */
const API_PREFIX = "/api";

/**
 * Check if a path matches any of the given patterns.
 */
function matchesPath(path: string, patterns: string[]): boolean {
  return patterns.some(
    (pattern) => path === pattern || path.startsWith(`${pattern}/`)
  );
}

/**
 * Middleware function to handle authentication and request modification.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;

  // Handle API requests - inject Authorization header if token exists
  if (pathname.startsWith(API_PREFIX)) {
    if (token) {
      // Clone the request and add Authorization header
      const requestHeaders = new Headers(request.headers);
      requestHeaders.set("Authorization", `Bearer ${token}`);

      return NextResponse.next({
        request: {
          headers: requestHeaders,
        },
      });
    }
    return NextResponse.next();
  }

  // Handle protected routes - redirect to login if not authenticated
  if (matchesPath(pathname, PROTECTED_ROUTES)) {
    if (!token) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  // Handle auth routes - redirect to dashboard if already authenticated
  if (matchesPath(pathname, AUTH_ROUTES)) {
    if (token) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
  }

  return NextResponse.next();
}

/**
 * Configure which routes the middleware should run on.
 */
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!_next/static|_next/image|favicon.ico|public/).*)",
  ],
};
