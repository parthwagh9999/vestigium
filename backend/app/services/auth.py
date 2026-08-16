"""Authentication service handling login, registration, and token management."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.exceptions import AlreadyExistsError, AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    validate_refresh_token,
    verify_password,
    TokenValidationError,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import LoginRequest, RegisterRequest, TokenResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.user_repo = UserRepository(session)

    async def register(self, data: RegisterRequest) -> User:
        """Register a new user account.

        Args:
            data: Registration data with username, email, password.

        Returns:
            The created User instance.

        Raises:
            AlreadyExistsError: If username or email is already taken.
        """
        if await self.user_repo.username_exists(data.username):
            raise AlreadyExistsError("User", "username", data.username)

        if await self.user_repo.email_exists(data.email):
            raise AlreadyExistsError("User", "email", data.email)

        user = await self.user_repo.create(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )

        logger.info("User registered: %s", user.username)
        return user

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate a user and return JWT tokens.

        Args:
            data: Login credentials (username/email + password).

        Returns:
            TokenResponse with access and refresh tokens.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        user = await self.user_repo.get_by_username_or_email(data.username)

        if user is None or not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid username or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        user.last_login = datetime.now(timezone.utc)
        await self.session.flush()

        access_token = create_access_token(
            subject=user.id,
            settings=self.settings,
            additional_claims={
                "username": user.username,
                "is_superuser": user.is_superuser,
            },
        )
        refresh_token = create_refresh_token(
            subject=user.id,
            settings=self.settings,
        )

        logger.info("User logged in: %s", user.username)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.settings.jwt_access_token_expire_minutes * 60,
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Exchange a refresh token for new access and refresh tokens.

        Args:
            refresh_token: The current refresh token.

        Returns:
            New TokenResponse with fresh tokens.

        Raises:
            AuthenticationError: If the refresh token is invalid.
        """
        try:
            user_id = validate_refresh_token(refresh_token, self.settings)
        except TokenValidationError as e:
            raise AuthenticationError(str(e.message)) from e

        user = await self.user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        new_access = create_access_token(
            subject=user.id,
            settings=self.settings,
            additional_claims={
                "username": user.username,
                "is_superuser": user.is_superuser,
            },
        )
        new_refresh = create_refresh_token(
            subject=user.id,
            settings=self.settings,
        )

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=self.settings.jwt_access_token_expire_minutes * 60,
        )
