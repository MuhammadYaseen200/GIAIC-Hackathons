"use server"

import { cookies } from "next/headers"
import { revalidatePath } from "next/cache"

interface ToolCall {
  name: string
  arguments: Record<string, unknown>
  result: string
}

interface ChatResponse {
  conversationId: string
  response: string
  toolCalls: ToolCall[]
}

export async function sendMessage(
  message: string,
  conversationId: string | null
): Promise<ChatResponse> {
  const cookieStore = await cookies()
  const token = cookieStore.get("auth-token")?.value

  if (!token) {
    throw new Error("Not authenticated")
  }

  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  })

  if (!res.ok) {
    throw new Error("Failed to send message")
  }

  const data = await res.json()

  // Revalidate task list if task-modifying tools were called
  const taskTools = ["add_task", "delete_task", "update_task", "complete_task"]
  if (data.tool_calls?.some((tc: any) => taskTools.includes(tc.name))) {
    revalidatePath("/dashboard")
  }

  return {
    conversationId: data.conversation_id,
    response: data.response,
    toolCalls: data.tool_calls || [],
  }
}
