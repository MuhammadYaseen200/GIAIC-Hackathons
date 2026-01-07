import { ChatContainer } from "@/components/chat/ChatContainer"

export default function ChatPage() {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Task Assistant</h1>
      <ChatContainer />
    </div>
  )
}
