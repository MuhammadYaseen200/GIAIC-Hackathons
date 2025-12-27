/**
 * Type definitions for RAG Chatbot API
 */

export interface Citation {
  title: string;
  url: string;
  chapter_id: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: Date;
}

export interface ChatRequest {
  question: string;
  session_id: string;
  chapter_context?: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  tokens_used: number;
}

export interface ErrorResponse {
  error: string;
  detail?: string;
}
