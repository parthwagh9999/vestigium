"""Declarative base with common mixins for all database models.

Provides timestamp tracking, soft-delete, and UUID primary keys as reusable
mixins that all domain models inherit from.
"""

from __future__ import annotations

from typing import Any
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text, func, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


@event.listens_for(Base, "init", propagate=True)
def init_model_uuid(target: Any, _args: Any, kwargs: dict[str, Any]) -> None:
    """Automatically populate UUID on instantiation if the model has an id attribute."""
    if hasattr(target, "id") and ("id" not in kwargs or kwargs.get("id") is None):
        target.id = str(uuid.uuid4())


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin that adds soft-delete capability via is_deleted flag."""

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )


class UUIDPrimaryKeyMixin:
    """Mixin that provides a UUID primary key."""

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )

    def __init__(self, **kwargs: Any) -> None:
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = str(uuid.uuid4())
        super().__init__(**kwargs)


class DescriptionMixin:
    """Mixin for models that have a name and description."""

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        default=None,
        nullable=True,
    )
