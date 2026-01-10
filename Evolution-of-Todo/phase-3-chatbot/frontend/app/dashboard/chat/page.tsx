"use client"

import { ChatKitComponent } from "@/components/chat/ChatKit"

// Get the ChatKit domain key from environment
const CHATKIT_DOMAIN_KEY = process.env.NEXT_PUBLIC_CHATKIT_KEY || ""
const API_URL = process.env.NEXT_PUBLIC_API_URL || ""

export default function ChatPage() {
  return (
    <div className="container mx-auto p-6 h-[calc(100vh-120px)]">
      <ChatKitComponent
        apiUrl={`${API_URL}/api/v1/chatkit`}
        domainKey={CHATKIT_DOMAIN_KEY}
        theme="light"
      />
    </div>
  )
}
