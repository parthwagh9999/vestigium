"""Generic CRUD repository providing common database operations.

All specific repositories inherit from this base, gaining standard
create, read, update, delete, list, and count operations.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async CRUD repository.

    Provides standard database operations that all domain repositories
    inherit. Supports soft-delete awareness, pagination, filtering,
    and sorting.

    Args:
        model: The SQLAlchemy model class this repository manages.
        session: The async database session.
    """

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, id: str) -> ModelType | None:
        """Get a single record by primary key.

        Args:
            id: The primary key value.

        Returns:
            The model instance or None if not found.
        """
        stmt = select(self.model).where(self.model.id == id)

        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)  # noqa: E712

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, ids: list[str]) -> list[ModelType]:
        """Get multiple records by primary keys.

        Args:
            ids: List of primary key values.

        Returns:
            List of found model instances.
        """
        if not ids:
            return []

        stmt = select(self.model).where(self.model.id.in_(ids))

        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)  # noqa: E712

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list(
        self,
        *,
        filters: list[Any] | None = None,
        offset: int = 0,
        limit: int = 50,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[ModelType]:
        """List records with optional filtering, pagination, and sorting.

        Args:
            filters: SQLAlchemy filter expressions.
            offset: Number of records to skip.
            limit: Maximum number of records to return.
            sort_by: Column name to sort by.
            sort_order: "asc" or "desc".

        Returns:
            List of model instances.
        """
        stmt = select(self.model)

        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)  # noqa: E712

        if filters:
            stmt = stmt.where(and_(*filters))

        if sort_by and hasattr(self.model, sort_by):
            column = getattr(self.model, sort_by)
            stmt = stmt.order_by(column.desc() if sort_order == "desc" else column.asc())
        elif hasattr(self.model, "created_at"):
            stmt = stmt.order_by(self.model.created_at.desc())

        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, *, filters: list[Any] | None = None) -> int:
        """Count records matching optional filters.

        Args:
            filters: SQLAlchemy filter expressions.

        Returns:
            Number of matching records.
        """
        stmt = select(func.count()).select_from(self.model)

        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)  # noqa: E712

        if filters:
            stmt = stmt.where(and_(*filters))

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, **kwargs: Any) -> ModelType:
        """Create a new record.

        Args:
            **kwargs: Column values for the new record.

        Returns:
            The created model instance.
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def create_many(self, items: list[dict[str, Any]]) -> list[ModelType]:
        """Create multiple records in a batch.

        Args:
            items: List of dictionaries with column values.

        Returns:
            List of created model instances.
        """
        instances = [self.model(**item) for item in items]
        self.session.add_all(instances)
        await self.session.flush()
        for instance in instances:
            await self.session.refresh(instance)
        return instances

    async def update(self, id: str, **kwargs: Any) -> ModelType | None:
        """Update a record by ID.

        Args:
            id: The primary key of the record to update.
            **kwargs: Column values to update (None values are skipped).

        Returns:
            The updated model instance or None if not found.
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(instance, key):
                setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: str, *, hard: bool = False) -> bool:
        """Delete a record by ID.

        Supports both soft-delete (setting is_deleted=True) and
        hard delete (removing from database).

        Args:
            id: The primary key of the record to delete.
            hard: If True, physically removes the record.

        Returns:
            True if the record was found and deleted.
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return False

        if hard or not hasattr(instance, "is_deleted"):
            await self.session.delete(instance)
        else:
            from datetime import datetime, timezone
            instance.is_deleted = True
            instance.deleted_at = datetime.now(timezone.utc)

        await self.session.flush()
        return True

    async def exists(self, id: str) -> bool:
        """Check if a record exists by ID.

        Args:
            id: The primary key to check.

        Returns:
            True if the record exists.
        """
        stmt = select(func.count()).select_from(self.model).where(self.model.id == id)

        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)  # noqa: E712

        result = await self.session.execute(stmt)
        return result.scalar_one() > 0
