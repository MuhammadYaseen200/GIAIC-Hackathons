export function ToolCallBadge({ name }: { name: string }) {
  return (
    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-700">
      🛠️ {name}
    </span>
  )
}
