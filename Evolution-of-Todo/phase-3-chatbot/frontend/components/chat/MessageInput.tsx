"use client"
import { useState, FormEvent } from "react"

export interface MessageInputProps {
  onSend: (message: string) => void
  isLoading: boolean
}

export function MessageInput({ onSend, isLoading }: MessageInputProps) {
  const [input, setInput] = useState("")

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      onSend(input.trim())
      setInput("")
    }
  }

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t flex gap-2">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type a message..."
        disabled={isLoading}
        className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        type="submit"
        disabled={isLoading || !input.trim()}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? "..." : "Send"}
      </button>
    </form>
  )
}
