import { cookies } from "next/headers"
import { NextRequest, NextResponse } from "next/server"

// Defensive: trim and extract only the first part (before any spaces)
// This prevents "URL BACKEND_URL=..." concatenation bugs from malformed env vars
const BACKEND_URL = (process.env.BACKEND_URL || "http://localhost:8000").trim().split(' ')[0]

/**
 * Proxy handler for ChatKit API requests.
 *
 * This route proxies all ChatKit requests from the frontend to the backend,
 * avoiding CORS issues since ChatKit's iframe makes requests from cdn.platform.openai.com.
 *
 * The auth-token cookie is forwarded to the backend as an Authorization header.
 */
async function proxyRequest(request: NextRequest, path: string) {
  const cookieStore = await cookies()
  const token = cookieStore.get("auth-token")?.value

  // Build target URL
  const targetUrl = `${BACKEND_URL}/api/v1/chatkit/${path}`

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

  // Make request to backend
  const response = await fetch(targetUrl, {
    method: request.method,
    headers,
    body,
  })

  const contentType = response.headers.get("Content-Type") || "application/json"

  // Check if this is an SSE streaming response
  if (contentType.includes("text/event-stream") && response.body) {
    // For SSE: Stream the response directly without buffering
    // This is critical for real-time chat streaming to work
    return new NextResponse(response.body, {
      status: response.status,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
      },
    })
  }

  // For non-streaming responses: buffer and return normally
  const responseBody = await response.text()

  // Return response with CORS headers for the ChatKit iframe
  return new NextResponse(responseBody, {
    status: response.status,
    headers: {
      "Content-Type": contentType,
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    },
  })
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params
  return proxyRequest(request, path?.join("/") || "")
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params
  return proxyRequest(request, path?.join("/") || "")
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params
  return proxyRequest(request, path?.join("/") || "")
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params
  return proxyRequest(request, path?.join("/") || "")
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params
  return proxyRequest(request, path?.join("/") || "")
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
