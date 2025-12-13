"""
Google Gemini Service for RAG Chatbot
Handles embeddings generation and chat completions using Gemini API.
"""

import os
import logging
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
# from langchain.schema import HumanMessage, SystemMessage
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Manages Google Gemini API interactions for RAG chatbot.

    Provides:
    - Text embeddings (text-embedding-004, 768 dimensions)
    - Chat completions (gemini-1.5-flash)
    """

    def __init__(
        self,
        google_api_key: str | None = None,
        model: str = "gemini-1.5-flash",
        embedding_model: str = "models/text-embedding-004",
    ):
        """
        Initialize Gemini service with API credentials.

        Args:
            google_api_key: Google API key for Gemini
            model: Gemini chat model name
            embedding_model: Gemini embedding model name
        """
        self.api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable must be set")

        self.model_name = model
        self.embedding_model_name = embedding_model

        # Initialize chat model
        self.chat_model = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=0.7,
            max_tokens=1024,
        )

        # Initialize embeddings model
        self.embeddings_model = GoogleGenerativeAIEmbeddings(
            model=self.embedding_model_name,
            google_api_key=self.api_key,
        )

        logger.info(
            f"GeminiService initialized with chat_model={self.model_name}, "
            f"embedding_model={self.embedding_model_name}"
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate 768-dimensional embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            List of 768 floats representing the embedding vector

        Raises:
            Exception: If embedding generation fails
        """
        try:
            # GoogleGenerativeAIEmbeddings.embed_query returns a list of floats
            embedding = await self.embeddings_model.aembed_query(text)
            logger.debug(f"Generated embedding with dimension: {len(embedding)}")
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def generate_batch_embeddings(
        self, texts: List[str], batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of input texts
            batch_size: Number of texts to process per batch

        Returns:
            List of 768-dim embedding vectors (one per input text)

        Raises:
            Exception: If batch embedding fails
        """
        try:
            embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                batch_embeddings = await self.embeddings_model.aembed_documents(batch)
                embeddings.extend(batch_embeddings)
                logger.info(f"Processed batch {i // batch_size + 1}: {len(batch)} texts")

            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    async def generate_response(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        chapter_context: str | None = None,
    ) -> Dict[str, Any]:
        """
        Generate RAG response using retrieved context chunks.

        Args:
            question: User's question
            context_chunks: Retrieved text chunks from Qdrant with metadata
            chapter_context: Optional current chapter for context prioritization

        Returns:
            Dictionary with:
                - answer: Generated response text
                - tokens_used: Total token count
                - chunks_used: Number of chunks in context

        Raises:
            Exception: If response generation fails
        """
        try:
            # Build context from retrieved chunks
            context_text = "\n\n".join(
                [
                    f"[{chunk['metadata'].get('title', 'Unknown')}]\n{chunk['text']}"
                    for chunk in context_chunks
                ]
            )

            # System prompt for RAG chatbot
            system_prompt = """You are a Physical AI & Humanoid Robotics tutor embedded in an interactive textbook.

Your role:
1. Answer student questions using ONLY the provided textbook context
2. Cite specific chapters when referencing information
3. Provide code examples when relevant (use Python markdown blocks)
4. If the question is outside the textbook scope, politely redirect

Guidelines:
- Be concise but thorough (aim for 2-4 paragraphs)
- Use technical terminology correctly
- Always mention hardware requirements (laptop, GPU, Jetson) when relevant
- Format code blocks with proper syntax highlighting
- If context is insufficient, say so honestly

Context from textbook:
{context}"""

            # User prompt
            user_prompt = f"""Question: {question}

{"Current chapter: " + chapter_context if chapter_context else ""}

Provide a helpful answer based on the textbook context above."""

            # Generate response
            messages = [
                SystemMessage(content=system_prompt.format(context=context_text)),
                HumanMessage(content=user_prompt),
            ]

            response = await self.chat_model.ainvoke(messages)

            # Extract response text
            answer = response.content

            # Calculate token usage (approximate)
            # Gemini doesn't expose token count directly, so we estimate
            tokens_used = len(context_text.split()) + len(question.split()) + len(answer.split())

            return {
                "answer": answer,
                "tokens_used": tokens_used,
                "chunks_used": len(context_chunks),
            }

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Check Gemini API availability.

        Returns:
            bool: True if API is reachable and functional
        """
        try:
            # Test with simple embedding generation
            test_embedding = await self.generate_embedding("test")
            return len(test_embedding) == 768
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return False


# Global service instance (singleton pattern)
_gemini_service: GeminiService | None = None


def get_gemini_service() -> GeminiService:
    """
    Get or create the global GeminiService instance.

    Returns:
        GeminiService: Singleton Gemini service
    """
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
