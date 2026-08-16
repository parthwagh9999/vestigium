"""Authentication API endpoints — login, register, refresh tokens."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.session import get_async_session
from app.dependencies import get_cached_settings, get_current_active_user
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.audit import AuditService
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_cached_settings),
) -> User:
    """Register a new user account.

    Creates a new user with the provided credentials and returns
    the user profile (without sensitive fields).
    """
    auth_service = AuthService(session, settings)
    user = await auth_service.register(data)
    await session.commit()
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_cached_settings),
) -> TokenResponse:
    """Authenticate and receive JWT tokens.

    Returns an access token (short-lived) and refresh token (long-lived).
    """
    auth_service = AuthService(session, settings)
    tokens = await auth_service.login(data)

    audit = AuditService(session)
    await audit.log(
        action="login",
        resource_type="user",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await session.commit()

    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_cached_settings),
) -> TokenResponse:
    """Exchange a refresh token for new tokens."""
    auth_service = AuthService(session, settings)
    tokens = await auth_service.refresh_tokens(data.refresh_token)
    await session.commit()
    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get the current authenticated user's profile."""
    return current_user
