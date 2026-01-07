"use client"

export function ToolCallIndicator({ tool_calls }: { tool_calls?: string }) {
  if (!tool_calls) return null

  const tools = tool_calls.split(", ").map(t => t.trim()).filter(t => t)

  if (tools.length === 0) return null

  return (
    <div className="mt-2">
      <span className="text-xs font-semibold text-gray-600 mb-1 block">
        Tool calls:
      </span>
      <div className="flex gap-1 flex-wrap">
        {tools.map((tool, i) => (
          <span
            key={i}
            className="inline-flex items-center text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-md"
            title={tool}
          >
            <span className="mr-1" aria-hidden="true">
              🛠️
            </span>
            {tool}
          </span>
        ))}
      </div>
    </div>
  )
}
