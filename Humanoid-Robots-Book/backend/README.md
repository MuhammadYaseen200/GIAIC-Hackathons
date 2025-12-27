# RAG Chatbot Backend

FastAPI backend for the Physical AI & Humanoid Robotics textbook RAG chatbot.

## Features

- **RAG Pipeline**: Retrieval-Augmented Generation using Qdrant + Google Gemini
- **Vector Search**: Semantic search over 13 textbook chapters
- **Chat API**: POST `/api/chat` endpoint with citation support
- **Database Logging**: Chat history and query analytics in Neon Postgres
- **Health Checks**: `/health` endpoint for monitoring

## Technology Stack

- **Framework**: FastAPI 0.110+
- **Database**: Neon Serverless Postgres (SQLAlchemy async ORM)
- **Vector DB**: Qdrant Cloud (768-dim Gemini embeddings)
- **LLM**: Google Gemini 1.5 Flash (via LangChain)
- **Embeddings**: Google text-embedding-004 (768 dimensions)

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Google API key ([Get one here](https://aistudio.google.com/app/apikey))
- Qdrant Cloud account ([Free tier](https://cloud.qdrant.io))
- Neon Postgres database ([Free tier](https://neon.tech))

### 2. Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required environment variables**:
- `GOOGLE_API_KEY`: Your Google Gemini API key
- `QDRANT_URL`: Qdrant cluster URL
- `QDRANT_API_KEY`: Qdrant API key
- `DATABASE_URL`: Neon Postgres connection string

### 4. Database Setup

```bash
# Run migration
psql $DATABASE_URL -f db/migrations/002_rag_chatbot_schema.sql
```

Expected output:
```
CREATE EXTENSION
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
...
```

### 5. Create Qdrant Collection

```python
python -c "
from src.db.qdrant_setup import QdrantManager
manager = QdrantManager()
manager.create_collection()
print('✓ Qdrant collection created')
"
```

### 6. Ingest Textbook Content

```bash
# Dry run (test without uploading)
python scripts/ingest_docs.py --docs-dir ../docs --dry-run

# Actual ingestion
python scripts/ingest_docs.py --docs-dir ../docs
```

Expected output:
```
Processing chapter-5-digital-twin-intro.md...
  Created 3 chunks
  Generating embeddings...
  Processed batch 1: 3 texts
  Processed 3 chunks
...
Total documents processed: 65
Uploading to Qdrant...
Successfully uploaded 65 documents
```

### 7. Start Backend Server

```bash
uvicorn src.main:app --reload
```

Server runs at: `http://localhost:8000`

API docs: `http://localhost:8000/docs`

## API Endpoints

### POST /api/chat

Send a chat message and receive AI-generated response with citations.

**Request**:
```json
{
  "question": "How do I create a ROS 2 subscriber?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "chapter_context": "module-1-ros2-basics/chapter-2"
}
```

**Response**:
```json
{
  "answer": "To create a ROS 2 subscriber, inherit from `rclpy.node.Node`...",
  "citations": [
    {
      "title": "Chapter 2: Publisher-Subscriber Communication",
      "url": "../module-1-ros2-basics/chapter-2-pub-sub.md",
      "chapter_id": "module-1-ros2-basics/chapter-2"
    }
  ],
  "tokens_used": 1247
}
```

### GET /health

Check service health.

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "qdrant": "healthy",
    "gemini": "available"
  }
}
```

## Testing

### Manual API Testing

```bash
# Health check
curl http://localhost:8000/health

# Chat request
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is a digital twin?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Unit Tests

```bash
pytest tests/ -v --cov=src
```

## Project Structure

```
backend/
├── src/
│   ├── chat/
│   │   ├── routes.py          # FastAPI chat endpoints
│   │   ├── service.py         # RAG pipeline logic
│   │   ├── schemas.py         # Pydantic models
│   │   └── gemini_service.py  # Gemini API client
│   ├── db/
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── neon_client.py     # Neon Postgres client
│   │   └── qdrant_setup.py    # Qdrant manager
│   ├── config.py              # Settings management
│   └── main.py                # FastAPI app
├── scripts/
│   └── ingest_docs.py         # Document ingestion
├── db/migrations/
│   └── 002_rag_chatbot_schema.sql
├── requirements.txt
├── .env.example
└── README.md
```

## Configuration

### RAG Parameters

Edit in `.env`:

```bash
RAG_CHUNK_SIZE=512           # Tokens per chunk
RAG_CHUNK_OVERLAP=50         # Overlap between chunks
RAG_TOP_K=5                  # Number of chunks to retrieve
RAG_SCORE_THRESHOLD=0.7      # Minimum similarity score
```

### Gemini Models

```bash
GEMINI_MODEL=gemini-1.5-flash              # Chat model
GEMINI_EMBEDDING_MODEL=models/text-embedding-004  # 768-dim embeddings
```

## Troubleshooting

### Issue: "GOOGLE_API_KEY not found"

**Solution**: Ensure `.env` file exists and contains `GOOGLE_API_KEY`.

```bash
echo "GOOGLE_API_KEY=YOUR_KEY_HERE" >> .env
```

### Issue: "Qdrant connection failed"

**Solution**: Verify `QDRANT_URL` and `QDRANT_API_KEY` in `.env`.

```bash
# Test connection
curl -H "api-key: $QDRANT_API_KEY" $QDRANT_URL/collections
```

### Issue: "Database connection failed"

**Solution**: Check `DATABASE_URL` includes `sslmode=require` for Neon.

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host/db?sslmode=require
```

### Issue: "No chunks retrieved"

**Solution**: Run ingestion script to populate Qdrant.

```bash
python scripts/ingest_docs.py --docs-dir ../docs --recreate
```

## Deployment

### Railway Deployment

1. Create Railway project
2. Connect GitHub repo
3. Set environment variables in Railway dashboard
4. Deploy from `002-rag-chatbot` branch

```bash
# Verify deployment
curl https://your-app.railway.app/health
```

### Environment Variables for Production

```bash
NODE_ENV=production
DEBUG=false
ALLOWED_ORIGINS=https://your-username.github.io
```

## Performance

**Response Time**: <3 seconds (95th percentile)
**Concurrent Users**: Supports 100+ simultaneous requests
**Token Usage**: ~1000-2000 tokens per query

## Security

- API keys in environment variables (never committed)
- CORS whitelist for allowed origins
- Input validation via Pydantic models
- SQL injection prevention via SQLAlchemy ORM
- Rate limiting (future: implement slowapi)

## License

MIT License

## Support

For issues, see the main project README or [open an issue](https://github.com/your-username/Humanoid-Robots-Book/issues).
