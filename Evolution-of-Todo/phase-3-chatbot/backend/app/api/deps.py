"""FastAPI dependency injection for authentication and database sessions.

Provides:
- JWT token extraction from Authorization header or auth-token cookie
- Current user validation and retrieval
- Database session dependency
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import decode_access_token
from app.models.user import User
from app.services.auth_service import AuthService

# HTTP Bearer token security scheme (still available for direct API calls)
security = HTTPBearer()

# Type alias for session dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    request: Request,  # Add request parameter to access cookies
    session: SessionDep,
) -> User:
    """FastAPI dependency to get the current authenticated user.

    Extracts JWT token from Authorization header or auth-token cookie, validates it,
    and returns the associated user.

    Args:
        request: FastAPI request object to access cookies.
        session: Database session for user lookup.

    Returns:
        User: Authenticated user instance.

    Raises:
        HTTPException: 401 Unauthorized if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # First, try to get token from Authorization header
    token = None
    authorization = request.headers.get("Authorization")
    if authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:]

    # If no token in header, try to get from auth-token cookie
    if not token:
        token = request.cookies.get("auth-token")

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    auth_service = AuthService(session)
    user = await auth_service.get_user_by_id(user_id)

    if user is None:
        raise credentials_exception

    return user


# Type alias for current user dependency
CurrentUser = Annotated[User, Depends(get_current_user)]
