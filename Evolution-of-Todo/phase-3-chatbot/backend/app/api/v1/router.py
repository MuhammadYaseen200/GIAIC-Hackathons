"""API v1 router aggregation.

Combines all v1 API routers into a single router for inclusion in main app.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.chatkit import router as chatkit_router
from app.api.v1.chatkit_rest import router as chatkit_rest_router
from app.api.v1.tasks import router as tasks_router

# Main v1 router - aggregates all v1 endpoint routers
api_router = APIRouter()

# Include auth router (T027, T033-T035)
api_router.include_router(auth_router)

# Include tasks router (T040, T044, T045)
api_router.include_router(tasks_router)

# Include chat router (T-317, T-318, T-319)
api_router.include_router(chat_router)

# Include ChatKit REST wrapper router (Phase 2, T036)
# IMPORTANT: Must be registered BEFORE the JSON-RPC catch-all router so that
# explicit REST routes (e.g. /chatkit/sessions) take priority over /{path:path}
api_router.include_router(chatkit_rest_router, prefix="/chatkit")

# Include ChatKit JSON-RPC router (Phase 3 OpenAI ChatKit integration)
# This has a catch-all /{path:path} route that handles all ChatKit SDK requests
api_router.include_router(chatkit_router)
