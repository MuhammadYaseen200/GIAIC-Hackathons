"use client"

import { ChatKitComponent } from "@/components/chat/ChatKit"

// Get the ChatKit domain key from environment
const CHATKIT_DOMAIN_KEY = process.env.NEXT_PUBLIC_CHATKIT_KEY || ""

export default function ChatPage() {
  // Use relative URL for same-origin proxy to avoid CORS issues
  // The /api/chatkit route proxies to the backend
  const apiUrl = typeof window !== "undefined"
    ? `${window.location.origin}/api/chatkit`
    : "/api/chatkit"

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] w-full overflow-hidden">
      {/* Header - fixed height */}
      <div className="flex-shrink-0 mb-4 pb-4 border-b border-gray-200">
        <h1 className="text-2xl font-bold text-gray-900">AI Task Assistant</h1>
        <p className="text-sm text-gray-500 mt-1">
          Chat with your AI assistant to manage tasks using natural language
        </p>
      </div>

      {/* Chat Container - fills remaining space */}
      <div className="flex-1 min-h-0 bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
        <ChatKitComponent
          apiUrl={apiUrl}
          domainKey={CHATKIT_DOMAIN_KEY}
          theme="light"
        />
      </div>
    </div>
  )
}
