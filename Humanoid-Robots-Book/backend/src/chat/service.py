"""
Chat Service - RAG Pipeline Implementation
Core business logic for RAG chatbot with Gemini.
"""

import time
import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db.models import ChatSession, ChatMessage, QueryLog
from ..db.qdrant_setup import QdrantManager
from ..config import Settings
from .schemas import ChatRequest, Citation
from .gemini_service import GeminiService

logger = logging.getLogger(__name__)


class ChatService:
    """
    Manages RAG pipeline and database operations for chatbot.

    Responsibilities:
    - Generate embeddings for user questions
    - Retrieve relevant chunks from Qdrant
    - Generate responses using Gemini
    - Extract citations from retrieved chunks
    - Log queries to database
    """

    def __init__(
        self,
        db: AsyncSession,
        qdrant: QdrantManager,
        gemini: GeminiService,
        config: Settings,
    ):
        """
        Initialize chat service with dependencies.

        Args:
            db: Async database session
            qdrant: Qdrant manager for vector search
            gemini: Gemini service for embeddings and chat
            config: Application settings
        """
        self.db = db
        self.qdrant = qdrant
        self.gemini = gemini
        self.config = config

    async def process_chat_request(self, request: ChatRequest) -> Dict[str, Any]:
        """
        Process chat request through RAG pipeline.

        Pipeline:
        1. Ensure chat session exists
        2. Save user message to database
        3. Generate embedding for question
        4. Search Qdrant for relevant chunks
        5. Generate response using Gemini
        6. Extract citations
        7. Save assistant message to database
        8. Log query metrics

        Args:
            request: Chat request with question and session ID

        Returns:
            Dictionary with answer, citations, and tokens_used

        Raises:
            ValueError: If no relevant chunks found
            Exception: If pipeline fails
        """
        start_time = time.time()

        try:
            # Step 1: Ensure session exists
            session = await self._get_or_create_session(
                session_id=request.session_id,
                chapter_context=request.chapter_context,
            )

            # Step 2: Save user message
            user_message = ChatMessage(
                session_id=session.session_id,
                role="user",
                content=request.question,
                citations=None,
            )
            self.db.add(user_message)
            await self.db.flush()

            # Step 3: Generate embedding
            logger.info(f"Generating embedding for question: {request.question[:50]}...")
            query_embedding = await self.gemini.generate_embedding(request.question)

            # Step 4: Search Qdrant
            logger.info(
                f"Searching Qdrant (top_k={self.config.rag_top_k}, "
                f"threshold={self.config.rag_score_threshold})"
            )
            retrieved_chunks = await self.qdrant.search(
                query_vector=query_embedding,
                chapter_id=request.chapter_context,
                limit=self.config.rag_top_k,
                score_threshold=self.config.rag_score_threshold,
            )

            if not retrieved_chunks:
                raise ValueError(
                    "I couldn't find relevant information in the textbook to answer your question. "
                    "Try asking about ROS 2, Digital Twins, Isaac Sim, or VLA models."
                )

            logger.info(f"Retrieved {len(retrieved_chunks)} chunks")

            # Step 5: Generate response
            response_data = await self.gemini.generate_response(
                question=request.question,
                context_chunks=retrieved_chunks,
                chapter_context=request.chapter_context,
            )

            # Step 6: Extract citations
            citations = self._extract_citations(retrieved_chunks)

            # Step 7: Save assistant message
            assistant_message = ChatMessage(
                session_id=session.session_id,
                role="assistant",
                content=response_data["answer"],
                citations=[cite.model_dump() for cite in citations],
            )
            self.db.add(assistant_message)
            await self.db.flush()

            # Step 8: Log query metrics
            response_time_ms = int((time.time() - start_time) * 1000)
            avg_similarity = (
                sum(chunk["score"] for chunk in retrieved_chunks) / len(retrieved_chunks)
                if retrieved_chunks
                else None
            )

            query_log = QueryLog(
                session_id=session.session_id,
                question=request.question,
                answer=response_data["answer"],
                tokens_used=response_data["tokens_used"],
                response_time_ms=response_time_ms,
                chunks_retrieved=len(retrieved_chunks),
                avg_similarity_score=avg_similarity,
            )
            self.db.add(query_log)
            await self.db.commit()

            logger.info(f"Chat request completed successfully (time={response_time_ms}ms)")

            return {
                "answer": response_data["answer"],
                "citations": citations,
                "tokens_used": response_data["tokens_used"],
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in RAG pipeline: {e}", exc_info=True)
            raise

    async def _get_or_create_session(
        self,
        session_id: str,
        chapter_context: str | None = None,
    ) -> ChatSession:
        """
        Get existing session or create new one.

        Args:
            session_id: Session UUID
            chapter_context: Optional chapter context

        Returns:
            ChatSession instance
        """
        # Try to fetch existing session
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if session is None:
            # Create new session
            session = ChatSession(
                session_id=session_id,
                chapter_context=chapter_context,
            )
            self.db.add(session)
            await self.db.flush()
            logger.info(f"Created new session: {session_id}")
        else:
            # Update chapter context if provided
            if chapter_context and session.chapter_context != chapter_context:
                session.chapter_context = chapter_context
                await self.db.flush()

        return session

    def _extract_citations(self, chunks: List[Dict[str, Any]]) -> List[Citation]:
        """
        Extract citations from retrieved chunks.

        Args:
            chunks: Retrieved chunks with metadata

        Returns:
            List of Citation objects
        """
        citations = []
        seen_chapters = set()

        for chunk in chunks:
            chapter_id = chunk.get("chapter_id")
            if chapter_id and chapter_id not in seen_chapters:
                metadata = chunk.get("metadata", {})

                citation = Citation(
                    title=metadata.get("title", f"Chapter {chapter_id}"),
                    url=metadata.get("file_path", f"../docs/{chapter_id}.md"),
                    chapter_id=chapter_id,
                )
                citations.append(citation)
                seen_chapters.add(chapter_id)

        logger.info(f"Extracted {len(citations)} citations")
        return citations
