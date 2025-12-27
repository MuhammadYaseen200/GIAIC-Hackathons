# RAG Chatbot Quickstart Guide

**Feature**: RAG Chatbot (Physical AI Tutor)
**Created**: 2025-12-13
**Target Audience**: Developers implementing the chatbot feature

## Overview

This guide walks you through setting up the RAG Chatbot backend and frontend from scratch.

**Estimated Time**: 30 minutes (first-time setup)

---

## Prerequisites

Before starting, ensure you have:

### Required Accounts
- ✅ **OpenAI Account** with API key ([platform.openai.com](https://platform.openai.com))
- ✅ **Qdrant Cloud** free tier account ([cloud.qdrant.io](https://cloud.qdrant.io))
- ✅ **Neon Serverless Postgres** free tier ([neon.tech](https://neon.tech))

### Required Software
- ✅ **Node.js** 20+ (`node --version`)
- ✅ **Python** 3.11+ (`python --version`)
- ✅ **Git** (`git --version`)

### API Keys Checklist
```bash
# Verify you have these before proceeding:
# 1. OPENAI_API_KEY (starts with sk-...)
# 2. QDRANT_URL (https://xxxxx.qdrant.io)
# 3. QDRANT_API_KEY
# 4. DATABASE_URL (postgresql://...)
```

---

## Step 1: Clone Repository

```bash
cd /path/to/Humanoid-Robots-Book
git checkout 002-rag-chatbot  # Or your feature branch
```

---

## Step 2: Backend Setup

### 2.1 Install Python Dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

**Expected packages**:
- `fastapi>=0.110.0`
- `uvicorn[standard]>=0.27.0`
- `sqlalchemy[asyncio]>=2.0.0`
- `asyncpg>=0.29.0`  # Postgres async driver
- `qdrant-client>=1.7.0`
- `openai>=1.0.0`
- `pydantic>=2.0.0`
- `slowapi>=0.1.9`  # Rate limiting
- `tiktoken>=0.5.1`  # Tokenization
- `python-dotenv>=1.0.0`

### 2.2 Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:
```bash
# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Qdrant Cloud
QDRANT_URL=https://xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.us-east-1-0.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Neon Postgres
DATABASE_URL=postgresql+asyncpg://user:password@ep-xxxx-xxxx.us-east-2.aws.neon.tech/chatbot?sslmode=require

# CORS (add your GitHub Pages domain later)
ALLOWED_ORIGINS=http://localhost:3000,https://your-username.github.io
```

### 2.3 Run Database Migrations

```bash
# Option 1: Using migration SQL file
psql $DATABASE_URL -f db/migrations/002_rag_chatbot_schema.sql

# Option 2: Using Alembic (if configured)
alembic upgrade head
```

**Verify tables created**:
```bash
psql $DATABASE_URL -c "\dt"
```

Expected output:
```
             List of relations
 Schema |      Name       | Type  |  Owner
--------+-----------------+-------+---------
 public | chat_sessions   | table | user
 public | chat_messages   | table | user
 public | query_logs      | table | user
```

### 2.4 Create Qdrant Collection

```bash
# Run this Python script to initialize Qdrant
python -c "
import asyncio
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams
import os

async def setup():
    client = AsyncQdrantClient(
        url=os.getenv('QDRANT_URL'),
        api_key=os.getenv('QDRANT_API_KEY')
    )
    await client.create_collection(
        collection_name='textbook_chunks',
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
    )
    print('✓ Qdrant collection created')

asyncio.run(setup())
"
```

### 2.5 Start Backend Server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify API is running**:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-13T14:30:00Z",
  "dependencies": {
    "database": "connected",
    "vector_db": "connected",
    "openai": "available"
  }
}
```

---

## Step 3: Ingest Textbook Content

### 3.1 Run Ingestion Script

```bash
# From backend/ directory
python scripts/ingest_docs.py --docs-dir ../docs --dry-run
```

**What this does**:
1. Reads all Markdown files in `docs/` directory
2. Chunks content into 512-token segments with 50-token overlap
3. Generates embeddings using OpenAI `text-embedding-3-small`
4. Uploads to Qdrant with metadata

**Expected output** (dry-run):
```
Found 13 chapters to process
├── docs/module-1-ros2-basics/chapter-1-intro.md (3 chunks)
├── docs/module-1-ros2-basics/chapter-2-pub-sub.md (5 chunks)
├── docs/module-1-ros2-basics/chapter-3-services.md (4 chunks)
...
Total: 65 chunks, estimated cost: $0.0007

Run without --dry-run to proceed with ingestion.
```

### 3.2 Run Actual Ingestion

```bash
python scripts/ingest_docs.py --docs-dir ../docs
```

**Progress output**:
```
[1/13] Processing chapter-1-intro.md... ✓ (3 chunks)
[2/13] Processing chapter-2-pub-sub.md... ✓ (5 chunks)
...
[13/13] Processing chapter-13-deployment.md... ✓ (4 chunks)

✅ Ingestion complete!
   Chunks uploaded: 65
   Tokens processed: 33,280
   Cost: $0.0007
   Time: 2m 14s
```

### 3.3 Verify Ingestion

```bash
python -c "
import asyncio
from qdrant_client import AsyncQdrantClient
import os

async def verify():
    client = AsyncQdrantClient(
        url=os.getenv('QDRANT_URL'),
        api_key=os.getenv('QDRANT_API_KEY')
    )
    info = await client.get_collection('textbook_chunks')
    print(f'✓ Collection has {info.points_count} chunks')

asyncio.run(verify())
"
```

Expected: `✓ Collection has 65 chunks`

---

## Step 4: Frontend Setup

### 4.1 Install Frontend Dependencies

```bash
# From project root
npm install
```

**New dependencies** (should be in package.json):
```json
{
  "dependencies": {
    "@docusaurus/core": "^3.0.0",
    "@docusaurus/preset-classic": "^3.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "uuid": "^9.0.0"
  },
  "devDependencies": {
    "@types/uuid": "^9.0.0"
  }
}
```

### 4.2 Swizzle Docusaurus Root

```bash
npm run swizzle @docusaurus/theme-classic Root -- --wrap
```

Expected output:
```
✔ Created src/theme/Root.tsx
✔ Root component swizzled successfully
```

### 4.3 Create ChatWidget Component

**File**: `src/components/ChatWidget/index.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import './styles.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
}

interface Citation {
  title: string;
  url: string;
  chapter_id: string;
}

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sessionId] = useState(() => uuidv4());
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: input,
          session_id: sessionId
        })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer,
        citations: data.citations
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {!isOpen && (
        <button
          className="chat-widget-button"
          onClick={() => setIsOpen(true)}
          aria-label="Open chat"
        >
          💬
        </button>
      )}

      {isOpen && (
        <div className="chat-widget-container">
          <div className="chat-header">
            <h3>Physical AI Tutor</h3>
            <button onClick={() => setIsOpen(false)} aria-label="Close chat">✕</button>
          </div>

          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message message-${msg.role}`}>
                <div className="message-content">{msg.content}</div>
                {msg.citations && (
                  <div className="citations">
                    {msg.citations.map((cite, i) => (
                      <a key={i} href={cite.url} className="citation-link">
                        📖 {cite.title}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {loading && <div className="loading">Thinking...</div>}
          </div>

          <div className="chat-input">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask about the textbook..."
            />
            <button onClick={handleSend} disabled={loading}>Send</button>
          </div>
        </div>
      )}
    </>
  );
}
```

### 4.4 Start Frontend

```bash
npm start
```

Expected output:
```
[INFO] Starting the development server...
[SUCCESS] Docusaurus website is running at: http://localhost:3000/
```

---

## Step 5: Test End-to-End

### 5.1 Manual Testing

1. Open http://localhost:3000
2. Click chat widget button (bottom-right)
3. Type: "How do I create a ROS 2 subscriber?"
4. Verify response includes code example and citation link
5. Click citation link → Should navigate to Chapter 2

### 5.2 API Testing (cURL)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is a digital twin?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

Expected response:
```json
{
  "answer": "A **Digital Twin** is a virtual representation of a physical system...",
  "citations": [
    {
      "title": "Chapter 5: Digital Twin Introduction",
      "url": "../module-2-digital-twin/chapter-5-digital-twin-intro.md",
      "chapter_id": "module-2-digital-twin/chapter-5"
    }
  ],
  "tokens_used": 1523
}
```

### 5.3 Health Check

```bash
curl http://localhost:8000/health
```

Expected: All dependencies show "connected" or "available"

---

## Step 6: Common Issues

### Issue: "ModuleNotFoundError: No module named 'fastapi'"
**Solution**: Activate virtual environment
```bash
cd backend
source .venv/bin/activate
```

### Issue: "Could not connect to Qdrant"
**Solution**: Check `.env` has correct `QDRANT_URL` and `QDRANT_API_KEY`
```bash
# Test connection
curl -H "api-key: $QDRANT_API_KEY" $QDRANT_URL/collections
```

### Issue: "CORS error in browser console"
**Solution**: Add frontend URL to `ALLOWED_ORIGINS` in `.env`
```bash
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

Restart backend after changing `.env`

### Issue: "Rate limit exceeded" immediately
**Solution**: Clear slowapi cache (restart backend)
```bash
# Kill uvicorn
pkill -f uvicorn

# Restart
uvicorn src.main:app --reload
```

### Issue: Ingestion script fails with "OpenAI API error"
**Solution**: Verify API key is active
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

If error: Check API key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

---

## Step 7: Production Deployment

### 7.1 Backend (Railway)

1. Create Railway account
2. New Project → Deploy from GitHub
3. Select `Humanoid-Robots-Book` repo
4. Set environment variables in Railway dashboard:
   ```
   OPENAI_API_KEY=sk-...
   QDRANT_URL=https://...
   QDRANT_API_KEY=...
   DATABASE_URL=postgresql://...
   ALLOWED_ORIGINS=https://your-username.github.io
   ```
5. Deploy → Copy generated URL (e.g., `https://your-app.railway.app`)

### 7.2 Frontend (GitHub Pages)

1. Update `docusaurus.config.js`:
   ```javascript
   const config = {
     url: 'https://your-username.github.io',
     baseUrl: '/Humanoid-Robots-Book/',
     // ...
   };
   ```

2. Update `src/components/ChatWidget/index.tsx`:
   ```typescript
   const API_URL = process.env.NODE_ENV === 'production'
     ? 'https://your-app.railway.app'
     : 'http://localhost:8000';
   ```

3. Build and deploy:
   ```bash
   npm run build
   GIT_USER=your-username npm run deploy
   ```

---

## Step 8: Verify Success Criteria

Run these checks to confirm the chatbot meets spec requirements:

### SC-001: Response time <3s (95th percentile)
```bash
# Run 100 queries and measure latency
python scripts/benchmark.py --count 100
```

### SC-003: Citation links work 100%
```bash
# Test all citations navigate correctly
python scripts/test_citations.py
```

### SC-007: 100 concurrent users
```bash
# Load test with locust
locust -f tests/load_test.py --host http://localhost:8000
```

---

## Next Steps

1. **Implement Select-to-Ask**: Add text selection hook (see research.md Section 5)
2. **Add Markdown Rendering**: Use `react-markdown` for assistant responses
3. **Improve UI**: Add Tailwind CSS styling (see `skills/react-component.md`)
4. **Add Analytics**: Query logs dashboard with charts
5. **Run `/sp.tasks`**: Generate implementation tasks from this plan

---

## Resources

- **Spec**: `specs/002-rag-chatbot/spec.md`
- **Research**: `specs/002-rag-chatbot/research.md`
- **Data Model**: `specs/002-rag-chatbot/data-model.md`
- **API Contract**: `specs/002-rag-chatbot/contracts/openapi.yaml`
- **OpenAPI Docs**: http://localhost:8000/docs (once backend running)

---

**Quickstart Complete!** ✅

You now have a working RAG chatbot. Test it by asking: "What is ROS 2?" or "Show me a URDF example."
