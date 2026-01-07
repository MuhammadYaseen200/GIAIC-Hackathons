import { ToolCallBadge } from "./ToolCallBadge"

export interface MessageProps {
  role: "user" | "assistant"
  content: string
  toolCalls?: Array<{ name: string; result: string }>
}

export function Message({ role, content, toolCalls }: MessageProps) {
  const isUser = role === "user"

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[80%] rounded-lg p-3 ${
        isUser ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-900"
      }`}>
        <p className="whitespace-pre-wrap">{content}</p>
        {toolCalls && toolCalls.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {toolCalls.map((tc, i) => (
              <ToolCallBadge key={i} name={tc.name} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
