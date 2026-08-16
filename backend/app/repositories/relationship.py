"""Relationship repository with graph-aware queries."""

from __future__ import annotations

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.relationship import EntityRelationship
from app.repositories.base import BaseRepository


class RelationshipRepository(BaseRepository[EntityRelationship]):
    """Repository for EntityRelationship model."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(EntityRelationship, session)

    async def get_by_investigation(
        self,
        investigation_id: str,
        *,
        relationship_type: str | None = None,
        offset: int = 0,
        limit: int = 5000,
    ) -> list[EntityRelationship]:
        """Get relationships for an investigation.

        Args:
            investigation_id: The investigation ID.
            relationship_type: Optional type filter.
            offset: Pagination offset.
            limit: Maximum results.

        Returns:
            List of relationships.
        """
        filters = [EntityRelationship.investigation_id == investigation_id]
        if relationship_type:
            filters.append(EntityRelationship.relationship_type == relationship_type)
        return await self.list(filters=filters, offset=offset, limit=limit, sort_by="created_at")

    async def get_entity_relationships(
        self,
        entity_id: str,
    ) -> list[EntityRelationship]:
        """Get all relationships involving a specific entity.

        Args:
            entity_id: The entity ID.

        Returns:
            List of relationships where the entity is source or target.
        """
        result = await self.session.execute(
            select(EntityRelationship).where(
                or_(
                    EntityRelationship.source_entity_id == entity_id,
                    EntityRelationship.target_entity_id == entity_id,
                ),
                EntityRelationship.is_deleted == False,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def relationship_exists(
        self,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
    ) -> bool:
        """Check if a specific relationship already exists.

        Args:
            source_entity_id: Source entity ID.
            target_entity_id: Target entity ID.
            relationship_type: Relationship type.

        Returns:
            True if the relationship exists.
        """
        result = await self.session.execute(
            select(func.count()).select_from(EntityRelationship).where(
                EntityRelationship.source_entity_id == source_entity_id,
                EntityRelationship.target_entity_id == target_entity_id,
                EntityRelationship.relationship_type == relationship_type,
                EntityRelationship.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one() > 0

    async def get_type_distribution(self, investigation_id: str) -> dict[str, int]:
        """Get relationship type distribution.

        Args:
            investigation_id: The investigation ID.

        Returns:
            Dictionary mapping relationship types to counts.
        """
        result = await self.session.execute(
            select(
                EntityRelationship.relationship_type,
                func.count().label("count"),
            )
            .where(
                EntityRelationship.investigation_id == investigation_id,
                EntityRelationship.is_deleted == False,  # noqa: E712
            )
            .group_by(EntityRelationship.relationship_type)
        )
        return {row.relationship_type: row.count for row in result}

    async def upsert_relationship(self, **kwargs: Any) -> EntityRelationship:
        """Upsert a relationship based on investigation, source, target, and type.
        
        Args:
            **kwargs: Column values for the relationship.
            
        Returns:
            The created or updated relationship.
        """
        from sqlalchemy.dialects.sqlite import insert
        
        stmt = insert(EntityRelationship).values(**kwargs)
        
        # We only update confidence if it's higher, and weight if it's higher
        update_dict = {
            "confidence": func.max(EntityRelationship.confidence, stmt.excluded.confidence),
            "weight": func.max(EntityRelationship.weight, stmt.excluded.weight),
            "updated_at": func.current_timestamp(),
        }
        
        stmt = stmt.on_conflict_do_update(
            index_elements=["investigation_id", "source_entity_id", "target_entity_id", "relationship_type"],
            set_=update_dict,
        ).returning(EntityRelationship)
        
        result = await self.session.execute(stmt)
        return result.scalar_one()
