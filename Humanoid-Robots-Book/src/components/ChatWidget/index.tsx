/**
 * ChatWidget Component for RAG Chatbot
 * Floating chat interface with Gemini-powered responses
 */

// 


import React, { useState, useRef, useEffect } from 'react';
import BrowserOnly from '@docusaurus/BrowserOnly';

// Define the shape of a message
interface Message {
  role: 'user' | 'assistant';
  content: string;
}

// Helper to detect and render code blocks with copy button
function renderMessageContent(content: string) {
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    // Add text before code block
    if (match.index > lastIndex) {
      parts.push(
        <span key={`text-${lastIndex}`}>{content.substring(lastIndex, match.index)}</span>
      );
    }

    // Add code block with copy button
    const language = match[1] || 'code';
    const code = match[2];
    const codeId = `code-${match.index}`;

    parts.push(
      <div key={codeId} style={{ position: 'relative', marginTop: '8px', marginBottom: '8px' }}>
        <div style={{
          backgroundColor: '#2d2d2d',
          color: '#f8f8f2',
          padding: '12px',
          borderRadius: '6px',
          fontFamily: 'monospace',
          fontSize: '13px',
          overflowX: 'auto',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '8px',
            borderBottom: '1px solid #444',
            paddingBottom: '4px'
          }}>
            <span style={{ fontSize: '11px', color: '#888', textTransform: 'uppercase' }}>{language}</span>
            <button
              onClick={() => {
                navigator.clipboard.writeText(code);
                const btn = document.getElementById(`copy-btn-${match.index}`);
                if (btn) {
                  const original = btn.textContent;
                  btn.textContent = '✓ Copied';
                  setTimeout(() => { btn.textContent = original; }, 2000);
                }
              }}
              id={`copy-btn-${match.index}`}
              style={{
                background: 'rgba(255,255,255,0.1)',
                border: '1px solid rgba(255,255,255,0.2)',
                color: '#fff',
                padding: '4px 8px',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '11px',
                transition: 'background 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.2)'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
            >
              📋 Copy
            </button>
          </div>
          <code>{code}</code>
        </div>
      </div>
    );

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < content.length) {
    parts.push(
      <span key={`text-${lastIndex}`}>{content.substring(lastIndex)}</span>
    );
  }

  return parts.length > 0 ? parts : content;
}

function ChatWidgetContent() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    // 1. Add User Message to UI
    const userMsg: Message = { role: 'user', content: inputValue };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      // 2. Send Request to Backend
      // FIX: Ensure this matches the Pydantic model in backend/src/chat/schemas.py or routes.py
      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMsg.content, // Matches 'message' field
          history: [] // Matches optional 'history' field
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server Error: ${response.status}`);
      }

      const data = await response.json();

      // 3. Add Bot Response to UI
      const botMsg: Message = { role: 'assistant', content: data.response };
      setMessages((prev) => [...prev, botMsg]);

    } catch (error) {
      console.error('Chat error:', error);
      const errorMsg: Message = { role: 'assistant', content: 'Sorry, connection failed. Is the backend running on port 8000?' };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{ position: 'fixed', bottom: '20px', right: '20px', zIndex: 9999 }}>
      {/* Toggle Button */}
      {!isOpen && (
        <button 
          onClick={() => setIsOpen(true)}
          style={{
            padding: '16px', borderRadius: '50%', backgroundColor: '#25c2a0', 
            color: 'white', border: 'none', cursor: 'pointer', boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            fontSize: '24px'
          }}
        >
          💬
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div style={{
          width: '350px', height: '500px', backgroundColor: 'white', 
          border: '1px solid #ddd', borderRadius: '12px', display: 'flex', flexDirection: 'column',
          boxShadow: '0 8px 24px rgba(0,0,0,0.2)', overflow: 'hidden'
        }}>
          {/* Header */}
          <div style={{ padding: '12px', backgroundColor: '#25c2a0', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: 'bold' }}>AI Tutor</span>
            <button onClick={() => setIsOpen(false)} style={{ background: 'none', border: 'none', color: 'white', fontSize: '18px', cursor: 'pointer' }}>✕</button>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, padding: '12px', overflowY: 'auto', backgroundColor: '#f5f5f7' }}>
            {messages.length === 0 && <p style={{ textAlign: 'center', color: '#888', marginTop: '50%' }}>Ask me about Humanoid Robots!</p>}
            {messages.map((msg, idx) => (
              <div key={idx} style={{ marginBottom: '10px', textAlign: msg.role === 'user' ? 'right' : 'left' }}>
                <div style={{
                  display: 'inline-block', padding: '8px 12px', borderRadius: '12px',
                  backgroundColor: msg.role === 'user' ? '#25c2a0' : 'white',
                  color: msg.role === 'user' ? 'white' : '#333',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.1)', maxWidth: '85%', wordWrap: 'break-word'
                }}>
                  {msg.role === 'assistant' ? renderMessageContent(msg.content) : msg.content}
                </div>
              </div>
            ))}
            {isLoading && <div style={{ textAlign: 'left', color: '#888', fontSize: '12px', marginLeft: '10px' }}>Thinking...</div>}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div style={{ padding: '12px', borderTop: '1px solid #eee', backgroundColor: 'white', display: 'flex' }}>
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a question..."
              style={{ flex: 1, padding: '8px', borderRadius: '20px', border: '1px solid #ddd', outline: 'none', paddingLeft: '12px' }}
            />
            <button onClick={sendMessage} style={{ marginLeft: '8px', padding: '8px 16px', backgroundColor: '#25c2a0', color: 'white', border: 'none', borderRadius: '20px', cursor: 'pointer' }}>
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ChatWidget() {
  return (
    <BrowserOnly>
      {() => <ChatWidgetContent />}
    </BrowserOnly>
  );
}