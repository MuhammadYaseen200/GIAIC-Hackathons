-- Migration: 002_rag_chatbot_schema.sql
-- Description: Create tables for RAG chatbot (chat sessions, messages, query logs)
-- Created: 2025-12-13
-- Dependencies: PostgreSQL with UUID extension

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Table: chat_sessions
-- Description: Stores chat conversation sessions
-- ============================================================================

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    chapter_context TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for chat_sessions
CREATE INDEX IF NOT EXISTS idx_sessions_started ON chat_sessions(started_at DESC);

-- Comments for chat_sessions
COMMENT ON TABLE chat_sessions IS 'Chat conversation sessions';
COMMENT ON COLUMN chat_sessions.session_id IS 'Unique session identifier (UUID v4)';
COMMENT ON COLUMN chat_sessions.started_at IS 'Session creation timestamp';
COMMENT ON COLUMN chat_sessions.chapter_context IS 'Chapter ID user was reading (e.g., module-1-ros2-basics/chapter-2)';
COMMENT ON COLUMN chat_sessions.user_agent IS 'Browser user agent for analytics';
COMMENT ON COLUMN chat_sessions.created_at IS 'Record creation timestamp';

-- ============================================================================
-- Table: chat_messages
-- Description: Individual messages within chat sessions
-- ============================================================================

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL CHECK (LENGTH(content) BETWEEN 1 AND 10000),
    citations JSONB,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for chat_messages
CREATE INDEX IF NOT EXISTS idx_messages_session_time ON chat_messages(session_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON chat_messages(timestamp DESC);

-- Comments for chat_messages
COMMENT ON TABLE chat_messages IS 'Individual messages in chat conversations';
COMMENT ON COLUMN chat_messages.message_id IS 'Unique message identifier';
COMMENT ON COLUMN chat_messages.session_id IS 'Parent session ID (foreign key)';
COMMENT ON COLUMN chat_messages.role IS 'Message sender: user or assistant';
COMMENT ON COLUMN chat_messages.content IS 'Message text (markdown for assistant responses)';
COMMENT ON COLUMN chat_messages.citations IS 'Array of citation objects (assistant messages only)';
COMMENT ON COLUMN chat_messages.timestamp IS 'Message creation timestamp';
COMMENT ON COLUMN chat_messages.created_at IS 'Record creation timestamp';

-- ============================================================================
-- Table: query_logs
-- Description: Analytics logs for chatbot query performance
-- ============================================================================

CREATE TABLE IF NOT EXISTS query_logs (
    query_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(session_id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    tokens_used INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    chunks_retrieved INTEGER NOT NULL DEFAULT 5,
    avg_similarity_score FLOAT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for query_logs
CREATE INDEX IF NOT EXISTS idx_query_logs_timestamp ON query_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_query_logs_session ON query_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_response_time ON query_logs(response_time_ms);

-- Comments for query_logs
COMMENT ON TABLE query_logs IS 'Analytics records for chatbot query performance';
COMMENT ON COLUMN query_logs.query_id IS 'Unique log identifier';
COMMENT ON COLUMN query_logs.session_id IS 'Parent session (NULL if session deleted)';
COMMENT ON COLUMN query_logs.question IS 'User original question';
COMMENT ON COLUMN query_logs.answer IS 'Assistant response (without citations)';
COMMENT ON COLUMN query_logs.tokens_used IS 'Total tokens consumed (prompt + completion)';
COMMENT ON COLUMN query_logs.response_time_ms IS 'End-to-end latency in milliseconds';
COMMENT ON COLUMN query_logs.chunks_retrieved IS 'Number of vector chunks retrieved from Qdrant';
COMMENT ON COLUMN query_logs.avg_similarity_score IS 'Average cosine similarity of retrieved chunks';
COMMENT ON COLUMN query_logs.timestamp IS 'Query execution timestamp';
