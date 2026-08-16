"""FastAPI dependency injection functions.

Provides injectable dependencies for database sessions, current user,
permission checking, and settings access throughout the application.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.permissions import SystemPermission, get_user_permissions
from app.core.security import TokenValidationError, validate_access_token
from app.db.session import get_async_session
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_cached_settings() -> Settings:
    """Get cached application settings singleton.

    Returns:
        Settings instance (cached after first call).
    """
    return get_settings()


async def get_db(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session.

    This is a pass-through dependency that allows other dependencies
    to declare their session dependency clearly.

    Yields:
        An AsyncSession instance.
    """
    yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    session: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_cached_settings),
) -> User:
    """Dependency that extracts and validates the current user from the JWT token.

    Args:
        credentials: The Bearer token from the Authorization header.
        session: The database session.
        settings: Application settings.

    Returns:
        The authenticated User instance.

    Raises:
        HTTPException: If no token is provided or the token is invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = validate_access_token(credentials.credentials, settings)
    except TokenValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.message),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    result = await session.execute(
        select(User).where(User.id == user_id, User.is_deleted == False, User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that ensures the current user is active.

    Args:
        current_user: The authenticated user.

    Returns:
        The active User instance.

    Raises:
        HTTPException: If the user account is deactivated.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return current_user


async def get_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Dependency that ensures the current user is a superuser.

    Args:
        current_user: The authenticated active user.

    Returns:
        The superuser User instance.

    Raises:
        HTTPException: If the user is not a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )
    return current_user


class PermissionChecker:
    """Dependency class for checking user permissions.

    Usage:
        @router.get("/resource", dependencies=[Depends(PermissionChecker(SystemPermission.RESOURCE_READ))])
        async def get_resource():
            ...
    """

    def __init__(self, required_permission: SystemPermission) -> None:
        self.required_permission = required_permission

    async def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        """Check if the current user has the required permission.

        Args:
            current_user: The authenticated active user.

        Returns:
            The user if authorized.

        Raises:
            HTTPException: If the user lacks the required permission.
        """
        if current_user.is_superuser:
            return current_user

        user_permissions = get_user_permissions(current_user.roles)
        if self.required_permission.value not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{self.required_permission.value}' required",
            )

        return current_user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    session: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_cached_settings),
) -> User | None:
    """Dependency that optionally extracts the current user.

    Returns None if no valid token is provided instead of raising an error.
    Useful for endpoints that support both authenticated and anonymous access.

    Returns:
        The User instance or None.
    """
    if credentials is None:
        return None

    try:
        user_id = validate_access_token(credentials.credentials, settings)
    except TokenValidationError:
        return None

    result = await session.execute(
        select(User).where(User.id == user_id, User.is_deleted == False, User.is_active == True)  # noqa: E712
    )
    return result.scalar_one_or_none()
