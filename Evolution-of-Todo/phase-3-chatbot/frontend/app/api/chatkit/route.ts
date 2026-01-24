import { cookies } from "next/headers"
import { NextRequest, NextResponse } from "next/server"

// Defensive: trim and extract only the first part (before any spaces)
const BACKEND_URL = (process.env.BACKEND_URL || "http://localhost:8000").trim().split(' ')[0]

/**
 * Root handler for ChatKit API requests at /api/chatkit
 * This handles requests without any subpath.
 */
async function proxyRequest(request: NextRequest) {
  const cookieStore = await cookies()
  const token = cookieStore.get("auth-token")?.value

  // Build target URL (root chatkit endpoint)
  const targetUrl = `${BACKEND_URL}/api/v1/chatkit/`

  // Get request body if present
  let body: BodyInit | null = null
  if (request.method !== "GET" && request.method !== "HEAD") {
    body = await request.text()
  }

  // Forward headers, adding Authorization from cookie
  const headers = new Headers()
  headers.set("Content-Type", request.headers.get("Content-Type") || "application/json")
  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  console.log(`[ChatKit Proxy] ${request.method} ${targetUrl}`)

  // Make request to backend
  const response = await fetch(targetUrl, {
    method: request.method,
    headers,
    body,
  })

  // Get response body
  const responseBody = await response.text()

  console.log(`[ChatKit Proxy] Response: ${response.status}`)

  // Return response with CORS headers
  return new NextResponse(responseBody, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") || "application/json",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    },
  })
}

export async function GET(request: NextRequest) {
  return proxyRequest(request)
}

export async function POST(request: NextRequest) {
  return proxyRequest(request)
}

export async function PUT(request: NextRequest) {
  return proxyRequest(request)
}

export async function DELETE(request: NextRequest) {
  return proxyRequest(request)
}

export async function PATCH(request: NextRequest) {
  return proxyRequest(request)
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    },
  })
}
