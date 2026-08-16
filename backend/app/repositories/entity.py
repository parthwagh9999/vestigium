"""Entity repository with graph-aware queries and search."""

from __future__ import annotations

from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.repositories.base import BaseRepository


class EntityRepository(BaseRepository[Entity]):
    """Repository for Entity model with graph query operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Entity, session)

    async def get_by_investigation(
        self,
        investigation_id: str,
        *,
        entity_type: str | None = None,
        offset: int = 0,
        limit: int = 1000,
    ) -> list[Entity]:
        """Get entities for an investigation with optional type filter.

        Args:
            investigation_id: The investigation ID.
            entity_type: Optional entity type filter.
            offset: Pagination offset.
            limit: Maximum results.

        Returns:
            List of entities.
        """
        filters = [Entity.investigation_id == investigation_id]
        if entity_type:
            filters.append(Entity.entity_type == entity_type)
        return await self.list(filters=filters, offset=offset, limit=limit, sort_by="created_at")

    async def search(
        self,
        investigation_id: str | None = None,
        *,
        query: str | None = None,
        entity_types: list[str] | None = None,
        min_confidence: float | None = None,
        max_confidence: float | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Entity], int]:
        """Search entities with multiple filters.

        Args:
            investigation_id: Optional investigation scope.
            query: Text search query.
            entity_types: Filter by entity types.
            min_confidence: Minimum confidence threshold.
            max_confidence: Maximum confidence threshold.
            offset: Pagination offset.
            limit: Maximum results.

        Returns:
            Tuple of (matching entities, total count).
        """
        conditions = [Entity.is_deleted == False]  # noqa: E712

        if investigation_id:
            conditions.append(Entity.investigation_id == investigation_id)
        if entity_types:
            conditions.append(Entity.entity_type.in_(entity_types))
        if min_confidence is not None:
            conditions.append(Entity.confidence >= min_confidence)
        if max_confidence is not None:
            conditions.append(Entity.confidence <= max_confidence)
        if query:
            search_pattern = f"%{query}%"
            conditions.append(
                or_(
                    Entity.label.ilike(search_pattern),
                    Entity.value.ilike(search_pattern),
                    Entity.properties.ilike(search_pattern),
                )
            )

        count_stmt = select(func.count()).select_from(Entity).where(and_(*conditions))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        query_stmt = (
            select(Entity)
            .where(and_(*conditions))
            .order_by(Entity.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query_stmt)
        entities = list(result.scalars().all())

        return entities, total

    async def get_neighbors(self, entity_id: str) -> list[Entity]:
        """Get all entities directly connected to a given entity.

        Args:
            entity_id: The entity to find neighbors of.

        Returns:
            List of neighboring entities.
        """
        neighbor_ids_stmt = select(EntityRelationship.target_entity_id).where(
            EntityRelationship.source_entity_id == entity_id,
            EntityRelationship.is_deleted == False,  # noqa: E712
        ).union(
            select(EntityRelationship.source_entity_id).where(
                EntityRelationship.target_entity_id == entity_id,
                EntityRelationship.is_deleted == False,  # noqa: E712
            )
        )

        stmt = select(Entity).where(
            Entity.id.in_(neighbor_ids_stmt),
            Entity.is_deleted == False,  # noqa: E712
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_duplicates(
        self,
        investigation_id: str,
        value: str,
    ) -> list[Entity]:
        """Find potential duplicate entities by value and type.

        Args:
            investigation_id: The investigation to search in.
            value: The entity value to check.
            entity_type: The entity type.

        Returns:
            List of potential duplicates.
        """
        result = await self.session.execute(
            select(Entity).where(
                Entity.investigation_id == investigation_id,
                Entity.value == value,
                Entity.is_deleted == False,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def upsert_entity(self, **kwargs: Any) -> Entity:
        """Upsert an entity based on investigation_id, entity_type, and value.
        
        Args:
            **kwargs: Column values for the entity.
            
        Returns:
            The created or updated entity.
        """
        import json
        from sqlalchemy.dialects.sqlite import insert
        
        if "properties" in kwargs and isinstance(kwargs["properties"], dict):
            kwargs["properties"] = json.dumps(kwargs["properties"])
            
        stmt = insert(Entity).values(**kwargs)
        
        # We only update confidence if it's higher, and maybe properties (though complex in SQL, 
        # for now we update confidence and updated_at)
        update_dict = {
            "confidence": func.max(Entity.confidence, stmt.excluded.confidence),
            "updated_at": func.current_timestamp(),
        }
        
        stmt = stmt.on_conflict_do_update(
            index_elements=["investigation_id", "entity_type", "value"],
            set_=update_dict,
        ).returning(Entity)
        
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def bulk_update_positions(
        self,
        positions: list[dict[str, Any]],
    ) -> int:
        """Bulk update entity positions (for drag/drop).

        Args:
            positions: List of dicts with id, position_x, position_y.

        Returns:
            Number of entities updated.
        """
        count = 0
        for pos in positions:
            entity = await self.get_by_id(pos["id"])
            if entity:
                entity.position_x = pos["position_x"]
                entity.position_y = pos["position_y"]
                count += 1
        await self.session.flush()
        return count

    async def get_type_distribution(self, investigation_id: str) -> dict[str, int]:
        """Get entity type distribution for an investigation.

        Args:
            investigation_id: The investigation ID.

        Returns:
            Dictionary mapping entity types to counts.
        """
        result = await self.session.execute(
            select(Entity.entity_type, func.count().label("count"))
            .where(
                Entity.investigation_id == investigation_id,
                Entity.is_deleted == False,  # noqa: E712
            )
            .group_by(Entity.entity_type)
        )
        return {row.entity_type: row.count for row in result}
