"""
Pydantic Schemas for RAG Chatbot API
Defines request/response models with validation.
"""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class Citation(BaseModel):
    """
    Source citation for chatbot responses.

    Links back to textbook chapters for verification.
    """
    title: str = Field(..., description="Human-readable chapter title")
    url: str = Field(..., description="Relative URL to chapter markdown")
    chapter_id: str = Field(..., description="Unique chapter identifier")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Chapter 2: Publisher-Subscriber Communication",
                "url": "../module-1-ros2-basics/chapter-2-pub-sub.md",
                "chapter_id": "module-1-ros2-basics/chapter-2"
            }
        }
    }


class ChatRequest(BaseModel):
    """
    Request schema for POST /api/chat endpoint.

    Client sends user question with session ID and optional chapter context.
    """
    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="User's question about textbook content"
    )
    session_id: UUID = Field(
        ...,
        description="Client-generated session UUID (v4)"
    )
    chapter_context: Optional[str] = Field(
        None,
        description="Current chapter ID (e.g., 'module-1-ros2-basics/chapter-2')"
    )

    @field_validator("chapter_context")
    @classmethod
    def validate_chapter_context(cls, v: Optional[str]) -> Optional[str]:
        """Validate chapter context format if provided."""
        if v is not None and not v.startswith("module-"):
            raise ValueError(
                "chapter_context must start with 'module-' (e.g., 'module-1-ros2-basics/chapter-2')"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "How do I create a ROS 2 subscriber?",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "chapter_context": "module-1-ros2-basics/chapter-2"
                },
                {
                    "question": "What is a digital twin?",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "chapter_context": None
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    """
    Response schema for POST /api/chat endpoint.

    Returns AI-generated answer with citations and token usage.
    """
    answer: str = Field(
        ...,
        description="Markdown-formatted response from Gemini"
    )
    citations: List[Citation] = Field(
        ...,
        min_length=1,
        description="Source citations from textbook"
    )
    tokens_used: int = Field(
        ...,
        ge=0,
        description="Total tokens consumed (prompt + completion)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "answer": "To create a ROS 2 subscriber, inherit from `rclpy.node.Node` and use `create_subscription()`:\n\n```python\nclass MySubscriber(Node):\n    def __init__(self):\n        super().__init__('my_subscriber')\n        self.subscription = self.create_subscription(\n            String,\n            'topic_name',\n            self.listener_callback,\n            10\n        )\n```",
                "citations": [
                    {
                        "title": "Chapter 2: Publisher-Subscriber Communication",
                        "url": "../module-1-ros2-basics/chapter-2-pub-sub.md",
                        "chapter_id": "module-1-ros2-basics/chapter-2"
                    }
                ],
                "tokens_used": 1247
            }
        }
    }


class ErrorResponse(BaseModel):
    """
    Error response schema for all endpoints.

    Provides user-friendly error messages with optional details.
    """
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "Rate limit exceeded",
                    "detail": "Maximum 10 requests per minute. Try again in 45 seconds."
                },
                {
                    "error": "Validation error",
                    "detail": "Field 'question' exceeds maximum length of 500 characters"
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """
    Health check response schema.

    Reports service health and dependency status.
    """
    status: str = Field(..., description="Service status: 'healthy' or 'unhealthy'")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    dependencies: dict = Field(
        ...,
        description="Dependency statuses: database, vector_db, gemini"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "timestamp": "2025-12-13T14:30:00Z",
                "dependencies": {
                    "database": "connected",
                    "vector_db": "connected",
                    "gemini": "available"
                }
            }
        }
    }
