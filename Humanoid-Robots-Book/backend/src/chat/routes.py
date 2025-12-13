"""
Chat API Routes for RAG Chatbot
Implements POST /api/chat endpoint with RAG pipeline.
"""

# import time
# import logging
# from typing import List
# from fastapi import APIRouter, Depends, HTTPException, Request
# from sqlalchemy.ext.asyncio import AsyncSession
# from slowapi import Limiter
# from slowapi.util import get_remote_address

# from ..db.neon_client import get_async_session
# from ..db.qdrant_setup import get_qdrant_manager, QdrantManager
# from ..config import get_config, Settings
# from .schemas import ChatRequest, ChatResponse, Citation, ErrorResponse
# from .gemini_service import get_gemini_service, GeminiService
# from .service import ChatService

# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/api", tags=["chat"])

# # Rate limiter instance
# limiter = Limiter(key_func=get_remote_address)


# @router.post(
#     "/chat",
#     response_model=ChatResponse,
#     responses={
#         400: {"model": ErrorResponse, "description": "Invalid request"},
#         429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
#         500: {"model": ErrorResponse, "description": "Internal server error"},
#     },
#     summary="Send chat message",
#     description="""
#     Send a user question and receive an AI-generated response with citations.

#     **Rate Limit**: 10 requests per minute per IP address.
#     **Response Time**: Typically 1-3 seconds (95th percentile: <3s).
#     **Retrieval**: Top-5 most relevant chunks with cosine similarity ≥ 0.7.
#     """,
# )
# @limiter.limit("10/minute")
# async def chat_endpoint(
#     request_obj: Request,
#     request: ChatRequest,
#     db: AsyncSession = Depends(get_async_session),
#     qdrant: QdrantManager = Depends(get_qdrant_manager),
#     gemini: GeminiService = Depends(get_gemini_service),
#     config: Settings = Depends(get_config),
# ) -> ChatResponse:
#     """
#     Process chat request using RAG pipeline.

#     Pipeline:
#     1. Generate embedding from user question
#     2. Search Qdrant for top-k relevant chunks
#     3. Generate response using Gemini with context
#     4. Extract citations from retrieved chunks
#     5. Log query to database
#     6. Return response with citations and token count
#     """
#     start_time = time.time()

#     try:
#         # Initialize chat service
#         chat_service = ChatService(db=db, qdrant=qdrant, gemini=gemini, config=config)

#         # Process RAG pipeline
#         response_data = await chat_service.process_chat_request(request)

#         # Calculate response time
#         response_time_ms = int((time.time() - start_time) * 1000)
#         logger.info(
#             f"Chat request processed in {response_time_ms}ms "
#             f"(session={request.session_id}, tokens={response_data['tokens_used']})"
#         )

#         # Return formatted response
#         return ChatResponse(
#             answer=response_data["answer"],
#             citations=response_data["citations"],
#             tokens_used=response_data["tokens_used"],
#         )

#     except ValueError as e:
#         # Validation errors (e.g., no chunks retrieved)
#         logger.warning(f"Validation error: {e}")
#         raise HTTPException(status_code=400, detail=str(e))

#     except Exception as e:
#         # Unexpected errors
#         logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=500,
#             detail="An error occurred while processing your request. Please try again.",
#         )


from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from src.chat.gemini_service import GeminiService, get_gemini_service
from src.db.qdrant_setup import QdrantManager, get_qdrant_manager
from src.db.neon_client import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import get_settings, Settings  # <--- FIXED IMPORT

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []

class ChatResponse(BaseModel):
    response: str
    sources: List[dict]

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    gemini: GeminiService = Depends(get_gemini_service),
    qdrant: QdrantManager = Depends(get_qdrant_manager),
    db: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings) # <--- FIXED DEPENDENCY
):
    try:
        # 1. Get Embedding for the user's question
        query_vector = gemini.get_embedding(request.message)

        # 2. Search Qdrant for relevant textbook chunks
        search_results = qdrant.search(
            query_vector=query_vector, 
            limit=settings.top_k_retrieval
        )

        # 3. Build Context from search results
        context_text = ""
        sources = []
        for hit in search_results:
            context_text += f"{hit.payload['content']}\n\n"
            sources.append({
                "source": hit.payload.get("source", "Unknown"),
                "score": hit.score
            })

        # 4. Generate Answer using Gemini + Context
        answer = gemini.generate_response(
            query=request.message,
            context=context_text,
            history=request.history
        )

        return ChatResponse(response=answer, sources=sources)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))