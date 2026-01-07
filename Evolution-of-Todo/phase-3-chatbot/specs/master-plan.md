# Phase 3 Master Plan: AI Chatbot Integration

**Branch**: `phase-3-chatbot`
**Date**: 2026-01-04
**Spec**: `phase-3-chatbot/specs/master-plan.md`
**Predecessor**: Phase 2 Full-Stack Web Application (COMPLETE)

---

## Executive Summary

Phase 3 transforms the Evolution of Todo application from a traditional CRUD web app into an AI-powered conversational interface. Users will interact with their tasks through natural language, with an AI agent orchestrating MCP (Model Context Protocol) tools to perform task operations.

**Key Constraint**: Import, don't rewrite. The MCP Server MUST import existing services from `backend/app/services/` rather than duplicating logic.

---

## Constitution Compliance

| Layer | Constitution Mandate | Phase 3 Implementation |
|-------|---------------------|------------------------|
| Chat UI | OpenAI ChatKit | OpenAI ChatKit (React components) |
| AI Framework | OpenAI Agents SDK | OpenAI Agents SDK (configured for Gemini) |
| MCP Server | Official MCP SDK (Python) | `mcp` Python package |
| State | Stateless API + DB persistence | Conversation model in Neon PostgreSQL |

### Brownfield Protocol Adherence

Phase 3 extends Phase 2 by adding an AI layer on top of existing infrastructure:

```
Phase 2 Services (UNCHANGED)     Phase 3 Extensions (NEW)
--------------------------       -----------------------
app/services/task_service.py --> Imported by MCP Tools
app/services/auth_service.py --> Imported by Chat endpoint
app/models/task.py           --> Used by MCP Tools
app/models/user.py           --> Used by Chat endpoint
app/api/v1/tasks.py          --> Continues to serve REST API
```

---

## 1. Database Evolution (Priority & Tags)

### 1.1 Task Model Extension

The Phase 2 Task model is extended with priority and tags fields:

```python
# phase-3-chatbot/backend/app/models/task.py (EXTENDED)

from enum import Enum
from sqlalchemy import JSON
from sqlmodel import Field, SQLModel

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Task(SQLModel, table=True):
    # ... existing fields ...

    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Task priority level (high, medium, low)",
    )
    tags: list[str] = Field(
        default_factory=list,
        sa_type=JSON,
        description="Task categorization labels",
    )
```

### 1.2 Alembic Migration

```python
# alembic/versions/20260104_002_add_priority_tags.py

def upgrade():
    # Add priority enum type
    op.execute("CREATE TYPE priority AS ENUM ('high', 'medium', 'low')")

    # Add priority column with default
    op.add_column('tasks', sa.Column(
        'priority',
        sa.Enum('high', 'medium', 'low', name='priority'),
        server_default='medium',
        nullable=False
    ))

    # Add tags column (JSONB for PostgreSQL)
    op.add_column('tasks', sa.Column(
        'tags',
        sa.JSON(),
        server_default='[]',
        nullable=False
    ))

def downgrade():
    op.drop_column('tasks', 'tags')
    op.drop_column('tasks', 'priority')
    op.execute("DROP TYPE priority")
```

### 1.3 TaskService Extension

```python
# phase-3-chatbot/backend/app/services/task_service.py (EXTENDED)

class TaskService:
    async def create_task(
        self,
        user_id: UUID,
        title: str,
        description: str = "",
        priority: Priority = Priority.MEDIUM,  # NEW
        tags: list[str] | None = None,  # NEW
    ) -> Task:
        """Create a new task with priority and tags."""
        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            tags=tags or [],
        )
        self.session.add(task)
        return task

    async def update_priority(
        self,
        user_id: UUID,
        task_id: UUID,
        priority: Priority,
    ) -> Task | None:
        """Update task priority."""
        task = await self.get_task(user_id, task_id)
        if task:
            task.priority = priority
        return task

    async def add_tags(
        self,
        user_id: UUID,
        task_id: UUID,
        tags: list[str],
    ) -> Task | None:
        """Add tags to a task (max 10)."""
        task = await self.get_task(user_id, task_id)
        if task:
            new_tags = list(set(task.tags + tags))[:10]
            task.tags = new_tags
        return task

    async def remove_tags(
        self,
        user_id: UUID,
        task_id: UUID,
        tags: list[str],
    ) -> Task | None:
        """Remove tags from a task."""
        task = await self.get_task(user_id, task_id)
        if task:
            task.tags = [t for t in task.tags if t not in tags]
        return task

    async def search_tasks(
        self,
        user_id: UUID,
        keyword: str | None = None,
        status: str | None = None,
        priority: Priority | None = None,
        tag: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[Task]:
        """Search and filter tasks with sorting."""
        query = select(Task).where(Task.user_id == user_id)

        if keyword:
            query = query.where(
                or_(
                    Task.title.ilike(f"%{keyword}%"),
                    Task.description.ilike(f"%{keyword}%"),
                )
            )

        if status == "pending":
            query = query.where(Task.completed == False)
        elif status == "completed":
            query = query.where(Task.completed == True)

        if priority:
            query = query.where(Task.priority == priority)

        if tag:
            query = query.where(Task.tags.contains([tag]))

        # Sorting
        order_col = getattr(Task, sort_by, Task.created_at)
        if sort_order == "asc":
            query = query.order_by(order_col.asc())
        else:
            query = query.order_by(order_col.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_user_tags(self, user_id: UUID) -> list[str]:
        """Get all unique tags used by a user."""
        tasks = await self.list_tasks(user_id)
        all_tags = set()
        for task in tasks:
            all_tags.update(task.tags)
        return sorted(all_tags)
```

---

## 2. MCP Server Design (Import Strategy)

### 2.1 Architecture Overview

The MCP Server is a NEW Python module that **imports and wraps** existing services without modification:

```python
# phase-3-chatbot/backend/app/mcp/tools/task_tools.py

from app.services.task_service import TaskService
from app.models.task import Task, Priority
from app.core.database import get_session

# Tool definitions wrap existing service methods
```

### 2.2 MCP Tool Definitions (Extended)

| Tool Name | Service Method | Input Schema | Output Schema |
|-----------|---------------|--------------|---------------|
| `add_task` | `TaskService.create_task()` | `{user_id, title, description?, priority?, tags?}` | `{task_id, status, title, priority, tags}` |
| `list_tasks` | `TaskService.search_tasks()` | `{user_id, status?, priority?, tag?, sort_by?, sort_order?}` | `[{id, title, completed, priority, tags, ...}]` |
| `complete_task` | `TaskService.toggle_complete()` | `{user_id, task_id}` | `{task_id, status, title}` |
| `delete_task` | `TaskService.delete_task()` | `{user_id, task_id}` | `{task_id, status, title}` |
| `update_task` | `TaskService.update_task()` | `{user_id, task_id, title?, description?, priority?}` | `{task_id, status, title, priority}` |
| `search_tasks` | `TaskService.search_tasks()` | `{user_id, keyword, status?, priority?, tag?}` | `[{id, title, completed, priority, tags, ...}]` |
| `update_priority` | `TaskService.update_priority()` | `{user_id, task_id, priority}` | `{task_id, priority}` |
| `add_tags` | `TaskService.add_tags()` | `{user_id, task_id, tags}` | `{task_id, tags}` |
| `remove_tags` | `TaskService.remove_tags()` | `{user_id, task_id, tags}` | `{task_id, tags}` |
| `list_tags` | `TaskService.list_user_tags()` | `{user_id}` | `{tags: [...]}` |

### 2.3 MCP Server Implementation

```python
# phase-3-chatbot/backend/app/mcp/server.py

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from app.mcp.tools.task_tools import (
    add_task_tool,
    list_tasks_tool,
    complete_task_tool,
    delete_task_tool,
    update_task_tool,
)

server = Server("evolution-of-todo")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        add_task_tool,
        list_tasks_tool,
        complete_task_tool,
        delete_task_tool,
        update_task_tool,
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    # Route to appropriate tool handler
    handlers = {
        "add_task": handle_add_task,
        "list_tasks": handle_list_tasks,
        "complete_task": handle_complete_task,
        "delete_task": handle_delete_task,
        "update_task": handle_update_task,
    }
    return await handlers[name](arguments)
```

### 2.4 Tool Handler Pattern

Each tool handler follows this pattern:

```python
# phase-3-chatbot/backend/app/mcp/tools/task_tools.py

from uuid import UUID
from mcp.types import Tool, TextContent
from app.services.task_service import TaskService
from app.core.database import get_session

add_task_tool = Tool(
    name="add_task",
    description="Create a new task for the user",
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "format": "uuid"},
            "title": {"type": "string", "minLength": 1, "maxLength": 200},
            "description": {"type": "string", "maxLength": 1000},
        },
        "required": ["user_id", "title"],
    },
)

async def handle_add_task(arguments: dict) -> list[TextContent]:
    async with get_session() as session:
        service = TaskService(session)
        task = await service.create_task(
            user_id=UUID(arguments["user_id"]),
            title=arguments["title"],
            description=arguments.get("description", ""),
        )
        await session.commit()
        return [TextContent(
            type="text",
            text=f"Created task '{task.title}' with ID {task.id}"
        )]
```

---

## 3. AI Stack Configuration

### 3.1 OpenAI Agents SDK with Google Gemini

The OpenAI Agents SDK will be configured to use Google Gemini as the underlying model. There are two architectural options:

#### Option A: OpenAI-Compatible Endpoint (RECOMMENDED)

Use Gemini through an OpenAI-compatible proxy or directly via the `openai` library with custom base URL:

```python
# phase-3-chatbot/backend/app/agent/chat_agent.py

from agents import Agent, Runner, ModelSettings
from agents.models.openai_compatible import OpenAICompatibleModel

# Configure Gemini via OpenAI-compatible interface
gemini_model = OpenAICompatibleModel(
    model="gemini-2.0-flash",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai",
    api_key=settings.GEMINI_API_KEY,
)

# Create agent with MCP tools
agent = Agent(
    name="TaskAssistant",
    instructions="""You are a helpful task management assistant.
    When users ask to manage their tasks, use the available tools.
    Always confirm actions and provide helpful summaries.""",
    model=gemini_model,
    tools=[
        "add_task",
        "list_tasks",
        "complete_task",
        "delete_task",
        "update_task",
    ],
)
```

#### Option B: Custom Model Adapter

If OpenAI-compatible endpoint is unavailable, create a custom adapter:

```python
# phase-3-chatbot/backend/app/agent/gemini_adapter.py

from agents.models import Model
import google.generativeai as genai

class GeminiModelAdapter(Model):
    """Adapter to use Google Gemini with OpenAI Agents SDK."""

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(model_name)

    async def generate(self, messages, tools=None, **kwargs):
        # Convert OpenAI message format to Gemini format
        # Handle tool calls and responses
        pass
```

### 3.2 Agent System Prompt

```python
SYSTEM_PROMPT = """You are TaskBot, an AI assistant for the Evolution of Todo application.

## Capabilities
You can help users manage their tasks through natural language. Available actions:
- Add new tasks (with title, optional description, priority, and tags)
- List all tasks (filter by status, priority, or tag)
- Mark tasks as complete/incomplete
- Update task details (title, description, priority)
- Delete tasks (always confirm first)
- Search tasks by keyword
- Manage tags (add, remove, list)
- Sort tasks (by priority, date, or name)

## Priority Levels
- HIGH: Critical, time-sensitive tasks
- MEDIUM: Normal importance (default)
- LOW: Nice to have, not urgent

## Behavior Guidelines
1. Always confirm before deleting tasks
2. Provide task summaries after operations (include priority/tags if set)
3. Be concise but helpful
4. If a user's request is ambiguous, ask clarifying questions
5. Report errors clearly and suggest alternatives
6. When listing tasks, show priority and tags for each
7. Default to medium priority when not specified

## Response Format
- Use bullet points for task lists
- Show priority with emoji: HIGH, MEDIUM, LOW
- Show tags in brackets: [Work] [Home]
- Include task IDs when referencing specific tasks
- Celebrate completions with encouragement
"""
```

### 3.3 Conversation State (Neon DB)

New model for conversation persistence:

```python
# phase-3-chatbot/backend/app/models/conversation.py

from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, JSON
from typing import Any

class Conversation(SQLModel, table=True):
    """Conversation history for AI chat sessions."""

    __tablename__ = "conversations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    messages: list[dict[str, Any]] = Field(default_factory=list, sa_type=JSON)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel):
    """Individual message in a conversation (not a table, stored in JSON)."""

    role: str  # "user" | "assistant" | "tool"
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

---

## 4. Backend API Extension

### 4.1 Chat Endpoint

```python
# phase-3-chatbot/backend/app/api/v1/chat.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_user
from app.agent.chat_agent import run_agent
from app.models.conversation import Conversation
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    conversation_id: Optional[UUID] = None
    message: str

class ToolCall(BaseModel):
    tool_name: str
    arguments: dict
    result: str

class ChatResponse(BaseModel):
    conversation_id: UUID
    response: str
    tool_calls: list[ToolCall] = []

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Process a chat message and return AI response."""

    # Load or create conversation
    conversation = await get_or_create_conversation(
        user_id=current_user.id,
        conversation_id=request.conversation_id,
    )

    # Run agent with user context
    result = await run_agent(
        user_id=current_user.id,
        conversation=conversation,
        message=request.message,
    )

    # Persist updated conversation
    await save_conversation(conversation)

    return ChatResponse(
        conversation_id=conversation.id,
        response=result.response,
        tool_calls=result.tool_calls,
    )
```

### 4.2 Router Integration

```python
# phase-3-chatbot/backend/app/api/v1/router.py (MODIFIED)

from fastapi import APIRouter
from app.api.v1 import auth, tasks, chat  # ADD chat import

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(tasks.router)
router.include_router(chat.router)  # ADD chat router
```

---

## 5. Frontend Integration

### 5.1 Chat Page Structure

```
frontend/
├── app/
│   └── dashboard/
│       ├── page.tsx              # Existing task list
│       └── chat/                 # NEW: Chat interface
│           └── page.tsx
├── components/
│   ├── chat/                     # NEW: Chat components
│   │   ├── ChatContainer.tsx     # Main chat wrapper
│   │   ├── MessageList.tsx       # Message history display
│   │   ├── MessageInput.tsx      # User input field
│   │   ├── Message.tsx           # Individual message
│   │   └── ToolCallIndicator.tsx # Shows when AI uses tools
│   └── ...
└── actions/
    └── chat.ts                   # NEW: Chat server action
```

### 5.2 Chat Components with OpenAI ChatKit

```typescript
// phase-3-chatbot/frontend/components/chat/ChatContainer.tsx

'use client';

import { useChat } from '@assistant-ui/react';  // OpenAI ChatKit
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';

export function ChatContainer() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/chat',
    initialMessages: [],
  });

  return (
    <div className="flex flex-col h-full">
      <MessageList messages={messages} isLoading={isLoading} />
      <MessageInput
        value={input}
        onChange={handleInputChange}
        onSubmit={handleSubmit}
        disabled={isLoading}
      />
    </div>
  );
}
```

### 5.3 Chat Server Action

```typescript
// phase-3-chatbot/frontend/app/actions/chat.ts

'use server';

import { cookies } from 'next/headers';
import { revalidatePath } from 'next/cache';

interface ChatResponse {
  conversation_id: string;
  response: string;
  tool_calls: Array<{
    tool_name: string;
    arguments: Record<string, unknown>;
    result: string;
  }>;
}

export async function sendMessage(
  message: string,
  conversationId?: string
): Promise<ChatResponse> {
  const cookieStore = await cookies();
  const token = cookieStore.get('auth-token')?.value;

  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${process.env.BACKEND_URL}/api/v1/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      message,
    }),
  });

  if (!response.ok) {
    throw new Error('Chat request failed');
  }

  const data = await response.json();

  // Revalidate tasks if any task-modifying tools were called
  const taskTools = ['add_task', 'complete_task', 'delete_task', 'update_task'];
  const usedTaskTool = data.tool_calls?.some(
    (tc: { tool_name: string }) => taskTools.includes(tc.tool_name)
  );

  if (usedTaskTool) {
    revalidatePath('/dashboard');
  }

  return data;
}
```

### 5.4 Dashboard Navigation Update

```typescript
// phase-3-chatbot/frontend/app/dashboard/layout.tsx (MODIFIED)

import Link from 'next/link';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen">
      <nav className="w-64 bg-gray-100 p-4">
        <ul className="space-y-2">
          <li>
            <Link href="/dashboard" className="...">
              Tasks
            </Link>
          </li>
          <li>
            <Link href="/dashboard/chat" className="...">
              Chat Assistant
            </Link>
          </li>
        </ul>
      </nav>
      <main className="flex-1">{children}</main>
    </div>
  );
}
```

---

## 6. System Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERACTION                                  │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js)                                                           │
│  ┌─────────────────────┐                                                      │
│  │   Chat Page         │                                                      │
│  │   /dashboard/chat   │                                                      │
│  └──────────┬──────────┘                                                      │
│             │ User types: "Add a task to buy groceries"                       │
│             ▼                                                                 │
│  ┌─────────────────────┐                                                      │
│  │   Server Action     │                                                      │
│  │   sendMessage()     │                                                      │
│  └──────────┬──────────┘                                                      │
└─────────────│────────────────────────────────────────────────────────────────┘
              │ POST /api/v1/chat { message: "Add a task to buy groceries" }
              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  BACKEND (FastAPI)                                                            │
│  ┌─────────────────────┐                                                      │
│  │   Chat Endpoint     │                                                      │
│  │   /api/v1/chat      │                                                      │
│  └──────────┬──────────┘                                                      │
│             │ Authenticate user, load conversation                            │
│             ▼                                                                 │
│  ┌─────────────────────┐                                                      │
│  │   Agent Runner      │◄────── OpenAI Agents SDK                             │
│  │   (Gemini Model)    │        configured with Gemini                        │
│  └──────────┬──────────┘                                                      │
│             │ Agent decides to call add_task tool                             │
│             ▼                                                                 │
│  ┌─────────────────────┐                                                      │
│  │   MCP Server        │                                                      │
│  │   Tool Router       │                                                      │
│  └──────────┬──────────┘                                                      │
│             │ Route to add_task handler                                       │
│             ▼                                                                 │
│  ┌─────────────────────┐     ┌─────────────────────┐                          │
│  │   Task Tools        │────►│   TaskService       │ (IMPORTED from Phase 2)  │
│  │   handle_add_task() │     │   create_task()     │                          │
│  └─────────────────────┘     └──────────┬──────────┘                          │
│                                         │                                     │
└─────────────────────────────────────────│─────────────────────────────────────┘
                                          │ INSERT INTO tasks
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  DATABASE (Neon PostgreSQL)                                                   │
│  ┌─────────────────────┐     ┌─────────────────────┐                          │
│  │   tasks             │     │   conversations     │                          │
│  │   (existing)        │     │   (NEW in Phase 3)  │                          │
│  └─────────────────────┘     └─────────────────────┘                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend (Next.js)
    participant SA as Server Action
    participant API as FastAPI /chat
    participant AG as Agent (Gemini)
    participant MCP as MCP Server
    participant TS as TaskService
    participant DB as Neon PostgreSQL

    U->>FE: Types "Add task: buy groceries"
    FE->>SA: sendMessage(message)
    SA->>API: POST /api/v1/chat
    API->>API: Authenticate (JWT)
    API->>DB: Load/create conversation
    API->>AG: Run agent with message
    AG->>AG: Parse intent: add_task
    AG->>MCP: call_tool("add_task", {title: "buy groceries"})
    MCP->>TS: TaskService.create_task(user_id, "buy groceries")
    TS->>DB: INSERT INTO tasks
    DB-->>TS: New task record
    TS-->>MCP: Task object
    MCP-->>AG: Tool result: "Created task..."
    AG->>AG: Generate response
    AG-->>API: "I've added 'buy groceries' to your tasks!"
    API->>DB: Save conversation with messages
    API-->>SA: ChatResponse
    SA->>SA: revalidatePath('/dashboard')
    SA-->>FE: Response
    FE-->>U: Display AI response
```

---

## 7. File Structure Plan

```
phase-3-chatbot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPI entry (ADD MCP mount)
│   │   │
│   │   ├── mcp/                         # NEW: MCP Server Module
│   │   │   ├── __init__.py
│   │   │   ├── server.py                # MCP Server entrypoint
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       └── task_tools.py        # 5 tool definitions
│   │   │
│   │   ├── agent/                       # NEW: Agent Module
│   │   │   ├── __init__.py
│   │   │   ├── chat_agent.py            # OpenAI Agents SDK + Gemini
│   │   │   ├── prompts.py               # System prompts
│   │   │   └── gemini_adapter.py        # (Optional) Custom adapter
│   │   │
│   │   ├── api/
│   │   │   ├── deps.py                  # Existing (no changes)
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py            # MODIFY: Add chat router
│   │   │       ├── auth.py              # Existing (no changes)
│   │   │       ├── tasks.py             # Existing (no changes)
│   │   │       └── chat.py              # NEW: Chat endpoint
│   │   │
│   │   ├── core/
│   │   │   ├── config.py                # MODIFY: Add GEMINI_API_KEY
│   │   │   ├── database.py              # Existing (no changes)
│   │   │   └── security.py              # Existing (no changes)
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py              # MODIFY: Export Conversation
│   │   │   ├── user.py                  # Existing (no changes)
│   │   │   ├── task.py                  # Existing (no changes)
│   │   │   └── conversation.py          # NEW: Conversation model
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── auth_service.py          # Existing (no changes)
│   │       ├── task_service.py          # Existing (IMPORTED by MCP)
│   │       └── conversation_service.py  # NEW: Conversation CRUD
│   │
│   ├── alembic/
│   │   └── versions/
│   │       └── 20260104_001_add_conversations.py  # NEW: Migration
│   │
│   └── pyproject.toml                   # MODIFY: Add new deps
│
├── frontend/
│   ├── app/
│   │   ├── dashboard/
│   │   │   ├── layout.tsx               # MODIFY: Add nav
│   │   │   ├── page.tsx                 # Existing task list
│   │   │   └── chat/                    # NEW: Chat page
│   │   │       └── page.tsx
│   │   │
│   │   └── actions/
│   │       ├── auth.ts                  # Existing (no changes)
│   │       ├── tasks.ts                 # Existing (no changes)
│   │       └── chat.ts                  # NEW: Chat action
│   │
│   ├── components/
│   │   ├── chat/                        # NEW: Chat components
│   │   │   ├── ChatContainer.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   ├── Message.tsx
│   │   │   └── ToolCallIndicator.tsx
│   │   │
│   │   ├── tasks/                       # Existing (no changes)
│   │   ├── auth/                        # Existing (no changes)
│   │   └── ui/                          # Existing (no changes)
│   │
│   └── package.json                     # MODIFY: Add @assistant-ui/react
│
├── specs/
│   ├── master-plan.md                   # THIS FILE
│   ├── tasks.md                         # MODIFY: Add Phase 3 tasks
│   └── api/
│       └── chat-endpoint.md             # NEW: Chat API spec
│
└── .env.example                         # MODIFY: Add GEMINI_API_KEY
```

---

## 8. Implementation Layers

### Layer 0: Configuration & Dependencies

| Task ID | Description | Files | Verification |
|---------|-------------|-------|--------------|
| T-301 | Add Phase 3 dependencies to pyproject.toml | `backend/pyproject.toml` | `uv sync` succeeds |
| T-302 | Add GEMINI_API_KEY to config | `backend/app/core/config.py`, `.env.example` | Settings load successfully |
| T-303 | Add frontend chat dependencies | `frontend/package.json` | `pnpm install` succeeds |

### Layer 1: Database Extension

| Task ID | Description | Files | Verification |
|---------|-------------|-------|--------------|
| T-304 | Create Priority enum and extend Task model | `backend/app/models/task.py` | Python import succeeds |
| T-305 | Create Alembic migration for priority/tags | `backend/alembic/versions/...` | `alembic upgrade head` succeeds |
| T-306 | Create Conversation model | `backend/app/models/conversation.py` | Python import succeeds |
| T-307 | Create Alembic migration for conversations | `backend/alembic/versions/...` | `alembic upgrade head` succeeds |
| T-308 | Create ConversationService | `backend/app/services/conversation_service.py` | Unit tests pass |
| T-309 | Extend TaskService with priority/tags methods | `backend/app/services/task_service.py` | Unit tests pass |

### Layer 2: MCP Server

| Task ID | Description | Files | Verification |
|---------|-------------|-------|--------------|
| T-310 | Create MCP tool definitions (5 core) | `backend/app/mcp/tools/task_tools.py` | Tools load without error |
| T-311 | Create MCP server | `backend/app/mcp/server.py` | Server starts, tools listed |
| T-312 | Write MCP tool handlers (core) | `backend/app/mcp/tools/task_tools.py` | Each tool executes successfully |
| T-313 | Add priority/tags MCP tools (5 new) | `backend/app/mcp/tools/task_tools.py` | Extended tools work |

### Layer 3: Agent Integration

| Task ID | Description | Files | Verification |
|---------|-------------|-------|--------------|
| T-314 | Create Gemini model configuration | `backend/app/agent/chat_agent.py` | Model responds to test prompt |
| T-315 | Create agent with MCP tools | `backend/app/agent/chat_agent.py` | Agent can call tools |
| T-316 | Create system prompts (with priority/tags) | `backend/app/agent/prompts.py` | Prompts load correctly |

### Layer 4: Chat API

| Task ID | Description | Files | Verification |
|---------|-------------|-------|--------------|
| T-317 | Create chat endpoint | `backend/app/api/v1/chat.py` | Endpoint responds |
| T-318 | Integrate chat router | `backend/app/api/v1/router.py` | Chat route accessible |
| T-319 | Wire agent to endpoint | `backend/app/api/v1/chat.py` | Full chat flow works |

### Layer 5: Frontend Chat UI

| Task ID | Description | Files | Verification |
|---------|-------------|-------|--------------|
| T-320 | Create chat components | `frontend/components/chat/*.tsx` | Components render |
| T-321 | Create chat page | `frontend/app/dashboard/chat/page.tsx` | Page accessible |
| T-322 | Create chat server action | `frontend/app/actions/chat.ts` | Action executes |
| T-323 | Update dashboard layout | `frontend/app/dashboard/layout.tsx` | Navigation works |

### Layer 6: Integration & Testing

| Task ID | Description | Files | Verification |
|---------|-------------|-------|--------------|
| T-324 | End-to-end chat flow (core) | - | User can chat, tasks created |
| T-325 | Priority via chat test | - | Priority set/updated correctly |
| T-326 | Tags via chat test | - | Tags added/removed correctly |
| T-327 | Search/filter via chat test | - | Search and filter work |
| T-328 | Task list sync | - | Task list updates after chat |

### Layer 7: Polish & Documentation

| Task ID | Description | Files | Verification |
|---------|-------------|-------|--------------|
| T-329 | Error handling in chat | All chat files | Errors displayed gracefully |
| T-330 | Loading states | Frontend components | Loading indicators work |
| T-331 | Create PHR for Phase 3 | `history/prompts/phase-3/...` | PHR exists |
| T-332 | Update CLAUDE.md | `CLAUDE.md` | Phase 3 documented |

---

## 9. Dependency Graph

```mermaid
flowchart TD
    subgraph L0["Layer 0: Configuration"]
        T301["T-301: Backend deps"]
        T302["T-302: Config"]
        T303["T-303: Frontend deps"]
    end

    subgraph L1["Layer 1: Database"]
        T304["T-304: Conversation model"]
        T305["T-305: Migration"]
        T306["T-306: ConversationService"]
    end

    subgraph L2["Layer 2: MCP Server"]
        T307["T-307: Tool definitions"]
        T308["T-308: MCP server"]
        T309["T-309: Tool handlers"]
    end

    subgraph L3["Layer 3: Agent"]
        T310["T-310: Gemini config"]
        T311["T-311: Agent + tools"]
        T312["T-312: Prompts"]
    end

    subgraph L4["Layer 4: Chat API"]
        T313["T-313: Chat endpoint"]
        T314["T-314: Router"]
        T315["T-315: Wire agent"]
    end

    subgraph L5["Layer 5: Frontend"]
        T316["T-316: Chat components"]
        T317["T-317: Chat page"]
        T318["T-318: Chat action"]
        T319["T-319: Dashboard nav"]
    end

    subgraph L6["Layer 6: Integration"]
        T320["T-320: E2E chat"]
        T321["T-321: Tool visibility"]
        T322["T-322: Task sync"]
    end

    subgraph L7["Layer 7: Polish"]
        T323["T-323: Error handling"]
        T324["T-324: Loading states"]
        T325["T-325: PHR"]
        T326["T-326: CLAUDE.md"]
    end

    T301 --> T304
    T301 --> T307
    T302 --> T310
    T303 --> T316

    T304 --> T305
    T305 --> T306

    T307 --> T308
    T308 --> T309

    T306 --> T313
    T309 --> T311
    T310 --> T311
    T312 --> T311

    T311 --> T315
    T313 --> T314
    T314 --> T315

    T316 --> T317
    T318 --> T317
    T319 --> T317

    T315 --> T320
    T317 --> T320
    T320 --> T321
    T320 --> T322

    T321 --> T323
    T322 --> T323
    T323 --> T324
    T324 --> T325
    T325 --> T326
```

---

## 10. New Dependencies

### Backend (pyproject.toml additions)

```toml
[project]
dependencies = [
    # ... existing dependencies ...

    # Phase 3: AI Chatbot
    "mcp>=1.0.0",                    # MCP Server SDK
    "openai-agents>=0.1.0",          # OpenAI Agents SDK
    "google-generativeai>=0.8.0",    # Gemini Python SDK (fallback)
]
```

### Frontend (package.json additions)

```json
{
  "dependencies": {
    "@assistant-ui/react": "^0.5.0"
  }
}
```

---

## 11. Environment Variables

```bash
# .env.example (additions for Phase 3)

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Agent Settings
AGENT_MAX_TURNS=10
AGENT_TIMEOUT_SECONDS=30
```

---

## 12. Acceptance Criteria

### Phase 3 is complete when:

1. **Database Extension**
   - [ ] Priority enum added to Task model
   - [ ] Tags JSON array added to Task model
   - [ ] Migrations run successfully on Neon
   - [ ] Existing tasks default to "medium" priority

2. **MCP Server**
   - [ ] All 10 tools defined and working (5 core + 5 extended)
   - [ ] Tools import from existing TaskService
   - [ ] No code duplication with Phase 2 services
   - [ ] Priority and tags passed through correctly

3. **Agent Integration**
   - [ ] Agent responds to natural language
   - [ ] Agent correctly selects and calls MCP tools
   - [ ] Gemini model successfully processes requests
   - [ ] Agent understands priority/tag commands

4. **Chat Endpoint**
   - [ ] POST /api/v1/chat accepts messages
   - [ ] Conversation state persists in database
   - [ ] Authentication required and enforced

5. **Frontend**
   - [ ] Chat page accessible at /dashboard/chat
   - [ ] Messages display correctly
   - [ ] Tool calls visible to user
   - [ ] Task list updates after chat operations

6. **Intermediate Features**
   - [ ] Add task with priority works
   - [ ] Update priority works
   - [ ] Add/remove tags works
   - [ ] Search by keyword works
   - [ ] Filter by priority/tag works
   - [ ] Sort by priority/date/name works

7. **Documentation**
   - [ ] PHR created for Phase 3
   - [ ] CLAUDE.md updated with Phase 3 completion

---

## 13. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| OpenAI Agents SDK incompatible with Gemini | Medium | High | Implement Option B (custom adapter) |
| MCP SDK breaking changes | Low | Medium | Pin version in pyproject.toml |
| Gemini rate limits | Medium | Medium | Implement retry logic with backoff |
| Frontend ChatKit complexity | Low | Low | Use simpler custom chat UI if needed |
| Conversation state bloat | Medium | Low | Add message limit per conversation |

---

## 14. ADR Candidates

The following decisions may warrant Architecture Decision Records:

| ID | Title | Trigger |
|----|-------|---------|
| ADR-008 | Gemini via OpenAI-Compatible Interface | If Option A chosen |
| ADR-009 | MCP Server as Embedded Module | Decided: Not standalone process |
| ADR-010 | Conversation Storage Strategy | JSON array vs. separate messages table |
| ADR-011 | Priority as Enum vs String | Enum chosen for type safety |
| ADR-012 | Tags as JSON Array | JSON chosen over junction table for simplicity |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-04 | @modular-ai-architect | Initial Phase 3 Master Plan |
| 2.0.0 | 2026-01-04 | @spec-architect | Added Intermediate Features (Priority, Tags, Search, Sort) |

---

**End of Phase 3 Master Plan**
