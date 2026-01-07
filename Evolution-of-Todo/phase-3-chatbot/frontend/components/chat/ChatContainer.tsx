"use client"
import { useState } from "react"
import { MessageList } from "./MessageList"
import { MessageInput } from "./MessageInput"
import { sendMessage } from "@/app/actions/chat"

interface Message {
  role: "user" | "assistant"
  content: string
  toolCalls?: Array<{ name: string; result: string }>
}

export function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([])
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleSend = async (content: string) => {
    setIsLoading(true)
    setMessages((prev) => [...prev, { role: "user", content }])

    try {
      const result = await sendMessage(content, conversationId)
      setConversationId(result.conversationId)
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.response, toolCalls: result.toolCalls }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-lg shadow-lg">
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold">Chat Assistant</h2>
      </div>
      <MessageList messages={messages} />
      <MessageInput onSend={handleSend} isLoading={isLoading} />
    </div>
  )
}
