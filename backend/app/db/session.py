"""Async database session management.

Provides session factories and context managers for database access
throughout the application.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Initialize the global async session factory.

    Args:
        engine: The SQLAlchemy async engine to bind sessions to.

    Returns:
        Configured async session factory.
    """
    global _session_factory
    _session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    return _session_factory


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the global session factory.

    Returns:
        The configured async session factory.

    Raises:
        RuntimeError: If the session factory has not been initialized.
    """
    if _session_factory is None:
        msg = "Session factory not initialized. Call init_session_factory() first."
        raise RuntimeError(msg)
    return _session_factory


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session.

    This is used as a FastAPI dependency for request-scoped sessions.
    The session is automatically committed on success and rolled back on error.

    Yields:
        An AsyncSession instance.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
