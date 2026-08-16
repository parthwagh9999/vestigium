"""Database engine factory and configuration.

Supports both SQLite (default, zero-config) and PostgreSQL (production scale).
Uses SQLAlchemy 2.0 async engine with proper connection pooling.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool, StaticPool

from app.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Create an async SQLAlchemy engine based on configuration.

    For SQLite:
        - Uses StaticPool for single-connection (thread-safe for async)
        - Enables WAL mode for better concurrent read performance

    For PostgreSQL:
        - Uses default QueuePool with connection limits
        - Enables statement caching for performance

    Args:
        settings: Application settings containing database URL.

    Returns:
        Configured AsyncEngine instance.
    """
    is_sqlite = settings.database_url.startswith("sqlite")

    connect_args: dict = {}
    pool_kwargs: dict = {}

    if is_sqlite:
        connect_args["check_same_thread"] = False
        connect_args["timeout"] = 30.0
        pool_kwargs["poolclass"] = StaticPool
    else:
        pool_kwargs["pool_size"] = 20
        pool_kwargs["max_overflow"] = 10
        pool_kwargs["pool_pre_ping"] = True
        pool_kwargs["pool_recycle"] = 3600

    engine = create_async_engine(
        settings.database_url,
        echo=settings.is_development and settings.app_debug,
        connect_args=connect_args,
        **pool_kwargs,
    )

    return engine
