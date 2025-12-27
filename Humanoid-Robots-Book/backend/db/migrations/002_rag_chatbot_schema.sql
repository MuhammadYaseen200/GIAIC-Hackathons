-- Migration: RAG Chatbot Schema
-- Created: 2025-12-13
-- Description: Creates tables for chat sessions, messages, and query logs

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- Chat Sessions Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    chapter_context TEXT,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE chat_sessions IS 'Chat conversation sessions initiated by users';
COMMENT ON COLUMN chat_sessions.session_id IS 'Unique session identifier (UUID v4)';
COMMENT ON COLUMN chat_sessions.started_at IS 'Session creation timestamp';
COMMENT ON COLUMN chat_sessions.chapter_context IS 'Chapter ID user was reading (e.g., module-1-ros2-basics/chapter-2)';
COMMENT ON COLUMN chat_sessions.user_agent IS 'Browser user agent for analytics';

-- ============================================================================
-- Chat Messages Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL CHECK (LENGTH(content) BETWEEN 1 AND 10000),
    citations JSONB,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE chat_messages IS 'Individual messages in chat conversations';
COMMENT ON COLUMN chat_messages.message_id IS 'Unique message identifier';
COMMENT ON COLUMN chat_messages.session_id IS 'Parent session ID';
COMMENT ON COLUMN chat_messages.role IS 'Message sender: user or assistant';
COMMENT ON COLUMN chat_messages.content IS 'Message text (markdown for assistant)';
COMMENT ON COLUMN chat_messages.citations IS 'Array of citation objects (assistant only)';

-- ============================================================================
-- Query Logs Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS query_logs (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(session_id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    tokens_used INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    chunks_retrieved INTEGER NOT NULL DEFAULT 5,
    avg_similarity_score FLOAT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE query_logs IS 'Analytics records for chatbot query performance';
COMMENT ON COLUMN query_logs.query_id IS 'Unique log identifier';
COMMENT ON COLUMN query_logs.session_id IS 'Parent session (NULL if session deleted)';
COMMENT ON COLUMN query_logs.question IS 'User original question';
COMMENT ON COLUMN query_logs.answer IS 'Assistant response (without citations)';
COMMENT ON COLUMN query_logs.tokens_used IS 'Total tokens (prompt + completion)';
COMMENT ON COLUMN query_logs.response_time_ms IS 'End-to-end latency in milliseconds';
COMMENT ON COLUMN query_logs.chunks_retrieved IS 'Number of vector chunks retrieved';
COMMENT ON COLUMN query_logs.avg_similarity_score IS 'Average cosine similarity of retrieved chunks';

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_messages_session_time ON chat_messages(session_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_query_logs_session ON query_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_timestamp ON query_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON chat_sessions(started_at DESC);

-- JSONB index for citations search
CREATE INDEX IF NOT EXISTS idx_messages_citations ON chat_messages USING GIN (citations);

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check tables created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('chat_sessions', 'chat_messages', 'query_logs')
ORDER BY table_name;

-- Check indexes created
SELECT indexname, tablename
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
