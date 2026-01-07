import { Message } from "./Message"

export interface MessageListProps {
  messages: Array<{
    role: "user" | "assistant"
    content: string
    toolCalls?: Array<{ name: string; result: string }>
  }>
}

export function MessageList({ messages }: MessageListProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 && (
        <div className="text-center text-gray-500 mt-8">
          <p>Start a conversation to manage your tasks!</p>
          <p className="text-sm mt-2">Try: "Add a task to buy groceries"</p>
        </div>
      )}
      {messages.map((msg, i) => (
        <Message key={i} {...msg} />
      ))}
    </div>
  )
}
