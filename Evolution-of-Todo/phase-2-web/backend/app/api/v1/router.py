"""API v1 router aggregation.

Combines all v1 API routers into a single router for inclusion in main app.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router

# Main v1 router - aggregates all v1 endpoint routers
api_router = APIRouter()

# Include auth router (T027, T033-T035)
api_router.include_router(auth_router)

# Placeholder for tasks router to be added in subsequent tasks:
# - tasks_router: Task CRUD endpoints
# api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
