"use client"

export function LoadingIndicator() {
  return (
    <div className="flex items-start gap-3 bg-gray-50 border-l-4 border-gray-500 p-3 rounded-r-lg">
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <p className="text-xs font-semibold text-gray-700">
            AI Assistant
          </p>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  )
}
