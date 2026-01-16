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
    <div className="container mx-auto p-6 h-[calc(100vh-120px)]">
      <ChatKitComponent
        apiUrl={apiUrl}
        domainKey={CHATKIT_DOMAIN_KEY}
        theme="light"
      />
    </div>
  )
}
