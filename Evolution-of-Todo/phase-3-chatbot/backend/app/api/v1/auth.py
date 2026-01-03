"""Authentication API endpoints.

Provides endpoints for:
- POST /auth/register - User registration
- POST /auth/login - User authentication and token generation
- POST /auth/logout - Logout acknowledgment
- GET /auth/me - Get current authenticated user

Task References: T027, T033, T034, T035
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.core.security import create_access_token
from app.services.auth_service import AuthService

# =============================================================================
# Pydantic Schemas
# =============================================================================


class RegisterRequest(BaseModel):
    """Request schema for user registration.

    Attributes:
        email: Valid email address.
        password: Password (minimum 8 characters).
    """

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        """Validate password meets minimum length requirement."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    """Request schema for user login.

    Attributes:
        email: Valid email address.
        password: User's password.
    """

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Response schema for user data.

    Attributes:
        id: User's unique identifier (UUID as string).
        email: User's email address.
        created_at: Account creation timestamp (ISO format).
    """

    id: str
    email: str
    created_at: str


class AuthSuccessResponse(BaseModel):
    """Generic success response wrapper.

    Attributes:
        success: Always True for success responses.
        data: Response payload.
    """

    success: bool = True
    data: dict


class AuthErrorDetail(BaseModel):
    """Error detail schema.

    Attributes:
        code: Error code identifier.
        message: Human-readable error message.
    """

    code: str
    message: str


class AuthErrorResponse(BaseModel):
    """Error response wrapper.

    Attributes:
        success: Always False for error responses.
        error: Error details.
    """

    success: bool = False
    error: AuthErrorDetail


# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/auth", tags=["auth"])


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/register",
    response_model=AuthSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "model": AuthErrorResponse,
            "description": "Duplicate email or validation error",
        },
    },
)
async def register(
    request: RegisterRequest,
    session: SessionDep,
) -> AuthSuccessResponse:
    """Register a new user account.

    Creates a new user with the provided email and password.
    Password is hashed before storage.

    Args:
        request: Registration request with email and password.
        session: Database session dependency.

    Returns:
        AuthSuccessResponse: Registration success with user data.

    Raises:
        HTTPException: 400 if email is already registered.

    Task Reference: T027
    """
    auth_service = AuthService(session)

    try:
        user = await auth_service.register(
            email=request.email,
            password=request.password,
        )
        await session.commit()
    except ValueError as e:
        error_message = str(e)
        if "already registered" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "DUPLICATE_EMAIL",
                        "message": "Email is already registered",
                    },
                },
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": error_message,
                },
            },
        )

    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        created_at=user.created_at.isoformat(),
    )

    return AuthSuccessResponse(
        success=True,
        data={
            "user": user_response.model_dump(),
            "message": "Registration successful",
        },
    )


@router.post(
    "/login",
    response_model=AuthSuccessResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Invalid credentials"},
    },
)
async def login(
    request: LoginRequest,
    session: SessionDep,
) -> AuthSuccessResponse:
    """Authenticate user and return JWT token.

    Validates credentials and returns access token on success.

    Args:
        request: Login request with email and password.
        session: Database session dependency.

    Returns:
        AuthSuccessResponse: Login success with user data and token.

    Raises:
        HTTPException: 401 if credentials are invalid.

    Task Reference: T033
    """
    auth_service = AuthService(session)

    user = await auth_service.authenticate(
        email=request.email,
        password=request.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password",
                },
            },
        )

    # Create JWT token with user ID as subject
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=expires_delta,
    )

    # Calculate expiration timestamp
    expires_at = datetime.now(UTC) + expires_delta

    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        created_at=user.created_at.isoformat(),
    )

    return AuthSuccessResponse(
        success=True,
        data={
            "user": user_response.model_dump(),
            "token": access_token,
            "expires_at": expires_at.isoformat(),
        },
    )


@router.post(
    "/logout",
    response_model=AuthSuccessResponse,
)
async def logout() -> AuthSuccessResponse:
    """Logout current user.

    Note: JWT tokens are stateless. This endpoint acknowledges the logout
    request, but actual token invalidation is handled client-side by
    removing the token from storage.

    Returns:
        AuthSuccessResponse: Logout acknowledgment.

    Task Reference: T034
    """
    return AuthSuccessResponse(
        success=True,
        data={
            "message": "Logged out successfully",
        },
    )


@router.get(
    "/me",
    response_model=AuthSuccessResponse,
    responses={
        401: {
            "model": AuthErrorResponse,
            "description": "Unauthorized - invalid or missing token",
        },
    },
)
async def get_me(
    current_user: CurrentUser,
) -> AuthSuccessResponse:
    """Get current authenticated user.

    Requires valid JWT token in Authorization header.

    Args:
        current_user: Current user from JWT token (dependency injection).

    Returns:
        AuthSuccessResponse: Current user data.

    Raises:
        HTTPException: 401 if token is invalid or missing.

    Task Reference: T035
    """
    user_response = UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        created_at=current_user.created_at.isoformat(),
    )

    return AuthSuccessResponse(
        success=True,
        data={
            "user": user_response.model_dump(),
        },
    )
