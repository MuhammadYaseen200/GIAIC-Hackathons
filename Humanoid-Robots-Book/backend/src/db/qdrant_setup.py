"""
Qdrant Vector Database Setup and Management
Handles vector collection creation, indexing, and retrieval for RAG chatbot.
"""

# import os
# from typing import List, Dict, Any
# from qdrant_client import QdrantClient, AsyncQdrantClient
# from qdrant_client.models import (
#     Distance,
#     VectorParams,
#     PointStruct,
#     Filter,
#     FieldCondition,
#     MatchValue,
# )
# import logging

# logger = logging.getLogger(__name__)

# # Constants from ADR-003: RAG Chunking Strategy
# COLLECTION_NAME = "physical_ai_textbook"
# VECTOR_SIZE = 768  # Google Gemini text-embedding-004 dimensions
# DISTANCE_METRIC = Distance.COSINE
# CHUNK_SIZE = 512  # tokens
# CHUNK_OVERLAP = 50  # tokens


# class QdrantManager:
#     """
#     Manages Qdrant Cloud vector database for RAG.

#     Handles collection creation, document indexing, and semantic search.
#     Optimized for 1GB free tier with 512-token chunks.
#     Uses Google Gemini text-embedding-004 (768 dimensions).
#     """

#     def __init__(
#         self,
#         qdrant_url: str | None = None,
#         qdrant_api_key: str | None = None,
#     ):
#         """
#         Initialize Qdrant client.

#         Args:
#             qdrant_url: Qdrant Cloud cluster URL (e.g., https://xxx.qdrant.io)
#             qdrant_api_key: Qdrant API key for authentication
#         """
#         self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL")
#         self.qdrant_api_key = qdrant_api_key or os.getenv("QDRANT_API_KEY")

#         if not self.qdrant_url or not self.qdrant_api_key:
#             raise ValueError(
#                 "QDRANT_URL and QDRANT_API_KEY environment variables must be set"
#             )

#         # Sync client for setup operations
#         self.client = QdrantClient(
#             url=self.qdrant_url,
#             api_key=self.qdrant_api_key,
#             timeout=30,
#         )

#         # Async client for production queries
#         self.async_client = AsyncQdrantClient(
#             url=self.qdrant_url,
#             api_key=self.qdrant_api_key,
#             timeout=30,
#         )

#         logger.info("QdrantManager initialized successfully")

#     def create_collection(self, recreate: bool = False) -> None:
#         """
#         Create the Physical AI textbook vector collection.

#         Args:
#             recreate: If True, delete existing collection and recreate
#         """
#         try:
#             # Check if collection exists
#             collections = self.client.get_collections().collections
#             collection_exists = any(c.name == COLLECTION_NAME for c in collections)

#             if collection_exists and recreate:
#                 logger.warning(f"Deleting existing collection: {COLLECTION_NAME}")
#                 self.client.delete_collection(collection_name=COLLECTION_NAME)
#                 collection_exists = False

#             if not collection_exists:
#                 logger.info(f"Creating collection: {COLLECTION_NAME}")
#                 self.client.create_collection(
#                     collection_name=COLLECTION_NAME,
#                     vectors_config=VectorParams(
#                         size=VECTOR_SIZE,
#                         distance=DISTANCE_METRIC,
#                     ),
#                 )
#                 logger.info(f"Collection {COLLECTION_NAME} created successfully")

#                 # Create payload indexes for filtering
#                 self.client.create_payload_index(
#                     collection_name=COLLECTION_NAME,
#                     field_name="chapter_id",
#                     field_schema="keyword",
#                 )
#                 self.client.create_payload_index(
#                     collection_name=COLLECTION_NAME,
#                     field_name="module_id",
#                     field_schema="keyword",
#                 )
#                 logger.info("Payload indexes created")
#             else:
#                 logger.info(f"Collection {COLLECTION_NAME} already exists")

#         except Exception as e:
#             logger.error(f"Error creating collection: {e}")
#             raise

#     def index_documents(
#         self,
#         documents: List[Dict[str, Any]],
#         batch_size: int = 100,
#     ) -> int:
#         """
#         Index document chunks into Qdrant.

#         Args:
#             documents: List of document dictionaries with keys:
#                 - id: Unique chunk ID
#                 - vector: 768-dim embedding array (Gemini text-embedding-004)
#                 - chapter_id: Chapter identifier (e.g., "chapter-1")
#                 - module_id: Module identifier (e.g., "module-1-ros2")
#                 - text: Original text chunk
#                 - metadata: Additional metadata (title, section, etc.)
#             batch_size: Number of documents to upload per batch

#         Returns:
#             int: Number of documents indexed
#         """
#         try:
#             points = [
#                 PointStruct(
#                     id=doc["id"],
#                     vector=doc["vector"],
#                     payload={
#                         "chapter_id": doc["chapter_id"],
#                         "module_id": doc["module_id"],
#                         "text": doc["text"],
#                         "metadata": doc.get("metadata", {}),
#                     },
#                 )
#                 for doc in documents
#             ]

#             # Upload in batches
#             for i in range(0, len(points), batch_size):
#                 batch = points[i : i + batch_size]
#                 self.client.upsert(
#                     collection_name=COLLECTION_NAME,
#                     points=batch,
#                 )
#                 logger.info(f"Indexed batch {i // batch_size + 1}: {len(batch)} documents")

#             logger.info(f"Successfully indexed {len(documents)} documents")
#             return len(documents)

#         except Exception as e:
#             logger.error(f"Error indexing documents: {e}")
#             raise

#     async def search(
#         self,
#         query_vector: List[float],
#         chapter_id: str | None = None,
#         limit: int = 5,
#         score_threshold: float = 0.7,
#     ) -> List[Dict[str, Any]]:
#         """
#         Perform semantic search in the vector database.

#         Args:
#             query_vector: 768-dim query embedding (Gemini text-embedding-004)
#             chapter_id: Optional chapter filter (e.g., "chapter-1")
#             limit: Maximum number of results to return
#             score_threshold: Minimum similarity score (0-1)

#         Returns:
#             List of retrieved documents with text and metadata
#         """
#         try:
#             # Build filter for chapter-specific search
#             search_filter = None
#             if chapter_id:
#                 search_filter = Filter(
#                     must=[
#                         FieldCondition(
#                             key="chapter_id",
#                             match=MatchValue(value=chapter_id),
#                         )
#                     ]
#                 )

#             # Execute search
#             results = await self.async_client.search(
#                 collection_name=COLLECTION_NAME,
#                 query_vector=query_vector,
#                 query_filter=search_filter,
#                 limit=limit,
#                 score_threshold=score_threshold,
#             )

#             # Format results
#             retrieved_docs = [
#                 {
#                     "text": result.payload["text"],
#                     "chapter_id": result.payload["chapter_id"],
#                     "module_id": result.payload["module_id"],
#                     "metadata": result.payload.get("metadata", {}),
#                     "score": result.score,
#                 }
#                 for result in results
#             ]

#             logger.info(f"Search returned {len(retrieved_docs)} results")
#             return retrieved_docs

#         except Exception as e:
#             logger.error(f"Search error: {e}")
#             raise

#     def get_collection_stats(self) -> Dict[str, Any]:
#         """
#         Get collection statistics (document count, storage usage).

#         Returns:
#             Dictionary with collection stats
#         """
#         try:
#             collection_info = self.client.get_collection(collection_name=COLLECTION_NAME)
#             return {
#                 "collection_name": COLLECTION_NAME,
#                 "vectors_count": collection_info.vectors_count,
#                 "points_count": collection_info.points_count,
#                 "status": collection_info.status,
#             }
#         except Exception as e:
#             logger.error(f"Error getting collection stats: {e}")
#             raise

#     async def health_check(self) -> bool:
#         """
#         Check Qdrant connection health.

#         Returns:
#             bool: True if connection is healthy
#         """
#         try:
#             collections = await self.async_client.get_collections()
#             logger.info("Qdrant health check passed")
#             return True
#         except Exception as e:
#             logger.error(f"Qdrant health check failed: {e}")
#             return False

#     async def close(self) -> None:
#         """
#         Close async client connections.
#         """
#         await self.async_client.close()
#         logger.info("QdrantManager closed")


# # Global client instance (singleton pattern)
# _qdrant_manager: QdrantManager | None = None


# def get_qdrant_manager() -> QdrantManager:
#     """
#     Get or create the global QdrantManager instance.

#     Returns:
#         QdrantManager: Singleton Qdrant client
#     """
#     global _qdrant_manager
#     if _qdrant_manager is None:
#         _qdrant_manager = QdrantManager()
#     return _qdrant_manager


import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.config import settings

logger = logging.getLogger(__name__)

class QdrantManager:
    def __init__(self):
        # Connect to Qdrant Cloud
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=10
        )
        self.collection_name = settings.qdrant_collection_name

    # --- THIS WAS MISSING (The Cause of the Crash) ---
    async def health_check(self):
        """Checks if Qdrant is reachable"""
        try:
            # Simple ping: Ask for the list of collections
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    def search(self, query_vector, limit=5):
        """Search for relevant textbook chunks"""
        try:
            return self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

# Singleton instance helper
def get_qdrant_manager():
    return QdrantManager()