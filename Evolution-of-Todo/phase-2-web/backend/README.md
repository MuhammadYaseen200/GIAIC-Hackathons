# Todo Backend

FastAPI backend for the Evolution of Todo application (Phase 2).

## Quick Start

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn app.main:app --reload --port 8000

# Run migrations
uv run alembic upgrade head
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
