"""User repository with authentication-specific queries."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model with authentication-specific operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_username(self, username: str) -> User | None:
        """Find a user by username.

        Args:
            username: The username to search for.

        Returns:
            User instance or None.
        """
        result = await self.session.execute(
            select(User).where(
                User.username == username,
                User.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Find a user by email address.

        Args:
            email: The email to search for.

        Returns:
            User instance or None.
        """
        result = await self.session.execute(
            select(User).where(
                User.email == email,
                User.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get_by_username_or_email(self, identifier: str) -> User | None:
        """Find a user by username or email (for login).

        Args:
            identifier: Username or email address.

        Returns:
            User instance or None.
        """
        result = await self.session.execute(
            select(User).where(
                or_(User.username == identifier, User.email == identifier),
                User.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def username_exists(self, username: str) -> bool:
        """Check if a username is already taken.

        Args:
            username: The username to check.

        Returns:
            True if the username exists.
        """
        user = await self.get_by_username(username)
        return user is not None

    async def email_exists(self, email: str) -> bool:
        """Check if an email is already registered.

        Args:
            email: The email to check.

        Returns:
            True if the email exists.
        """
        user = await self.get_by_email(email)
        return user is not None
