"use client"

import { useEffect, useRef, useState } from "react"
import type { OpenAIChatKit, ChatKitOptions } from "@openai/chatkit"

interface ChatKitProps {
  /** The API endpoint URL for ChatKit */
  apiUrl: string
  /** The domain public key for ChatKit verification */
  domainKey: string
  /** Optional initial thread ID */
  initialThread?: string | null
  /** Optional theme configuration */
  theme?: "light" | "dark"
  /** Optional callback when thread changes */
  onThreadChange?: (threadId: string | null) => void
}

export function ChatKitComponent({
  apiUrl,
  domainKey,
  initialThread = null,
  theme = "light",
  onThreadChange,
}: ChatKitProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chatKitRef = useRef<OpenAIChatKit | null>(null)
  const [isReady, setIsReady] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    let mounted = true

    // Wait for the ChatKit custom element to be defined
    const initChatKit = async () => {
      try {
        // Wait for the custom element to be defined (from CDN script)
        if (!customElements.get("openai-chatkit")) {
          await customElements.whenDefined("openai-chatkit")
        }

        if (!mounted || !containerRef.current) return

        // Create the ChatKit web component
        const chatKit = document.createElement("openai-chatkit") as OpenAIChatKit
        chatKitRef.current = chatKit

        // Configure ChatKit options
        const options: ChatKitOptions = {
          api: {
            url: apiUrl,
            domainKey: domainKey,
            // Use custom fetch to include credentials for auth
            fetch: async (input: RequestInfo | URL, init?: RequestInit) => {
              const response = await fetch(input, {
                ...init,
                credentials: "include", // This ensures the auth-token cookie is sent
              })
              return response
            },
          },
          theme: theme,
          initialThread: initialThread,
          header: {
            enabled: true,
            title: {
              enabled: true,
              text: "Task Assistant",
            },
          },
          history: {
            enabled: true,
            showDelete: true,
            showRename: true,
          },
          startScreen: {
            greeting: "What can I help you with today?",
            prompts: [
              {
                label: "List my tasks",
                prompt: "Show me all my tasks",
                icon: "lucide:list",
              },
              {
                label: "Add a task",
                prompt: "Add a new task to buy groceries",
                icon: "lucide:plus",
              },
              {
                label: "Organize my work",
                prompt: "Help me organize my work tasks",
                icon: "lucide:briefcase",
              },
            ],
          },
          composer: {
            placeholder: "Ask about your tasks...",
          },
          threadItemActions: {
            feedback: true,
            retry: true,
          },
        }

        chatKit.setOptions(options)

        // Add event listeners
        chatKit.addEventListener("chatkit.ready", () => {
          if (mounted) {
            setIsReady(true)
            setError(null)
          }
        })

        chatKit.addEventListener("chatkit.error", (event) => {
          console.error("ChatKit error:", event.detail.error)
          if (mounted) {
            setError(event.detail.error.message)
          }
        })

        chatKit.addEventListener("chatkit.thread.change", (event) => {
          onThreadChange?.(event.detail.threadId)
        })

        // Apply styling
        chatKit.style.cssText = `
          width: 100%;
          height: 100%;
          display: block;
          border-radius: 8px;
          overflow: hidden;
        `

        // Append to container
        containerRef.current.appendChild(chatKit)
      } catch (err) {
        console.error("Failed to initialize ChatKit:", err)
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load ChatKit")
        }
      }
    }

    initChatKit()

    // Cleanup
    return () => {
      mounted = false
      if (chatKitRef.current && containerRef.current?.contains(chatKitRef.current)) {
        containerRef.current.removeChild(chatKitRef.current)
      }
      chatKitRef.current = null
    }
  }, [apiUrl, domainKey, initialThread, theme, onThreadChange])

  return (
    <div className="relative w-full h-full">
      {!isReady && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg">
          <div className="flex flex-col items-center gap-4">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-blue-200 rounded-full" />
              <div className="absolute top-0 left-0 w-16 h-16 border-4 border-blue-600 rounded-full animate-spin border-t-transparent" />
            </div>
            <div className="text-center">
              <p className="text-blue-700 font-medium">Initializing Chat</p>
              <p className="text-sm text-blue-500 mt-1">Connecting to AI Assistant...</p>
            </div>
          </div>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 rounded-lg">
          <div className="text-center p-8 max-w-md">
            <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <p className="text-red-700 font-semibold text-lg mb-2">Chat Unavailable</p>
            <p className="text-sm text-red-600 mb-4">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-6 rounded-lg transition-colors shadow-sm"
            >
              Retry Connection
            </button>
          </div>
        </div>
      )}
      <div
        ref={containerRef}
        className="w-full h-full"
        style={{ visibility: isReady ? "visible" : "hidden" }}
      />
    </div>
  )
}
