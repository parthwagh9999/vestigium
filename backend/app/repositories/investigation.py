"""Investigation repository with graph state management."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import Entity
from app.models.investigation import Investigation, InvestigationSnapshot, InvestigationVersion
from app.models.relationship import EntityRelationship
from app.repositories.base import BaseRepository


class InvestigationRepository(BaseRepository[Investigation]):
    """Repository for Investigation model with graph state operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Investigation, session)

    async def get_by_workspace(
        self,
        workspace_id: str,
        *,
        offset: int = 0,
        limit: int = 50,
        status: str | None = None,
    ) -> list[Investigation]:
        """Get investigations for a workspace with optional status filter.

        Args:
            workspace_id: The workspace ID.
            offset: Pagination offset.
            limit: Maximum results.
            status: Optional status filter.

        Returns:
            List of investigations.
        """
        filters = [Investigation.workspace_id == workspace_id]
        if status:
            filters.append(Investigation.status == status)
        return await self.list(filters=filters, offset=offset, limit=limit)

    async def get_entity_count(self, investigation_id: str) -> int:
        """Count entities in an investigation.

        Args:
            investigation_id: The investigation ID.

        Returns:
            Number of entities.
        """
        result = await self.session.execute(
            select(func.count()).select_from(Entity).where(
                Entity.investigation_id == investigation_id,
                Entity.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one()

    async def get_relationship_count(self, investigation_id: str) -> int:
        """Count relationships in an investigation.

        Args:
            investigation_id: The investigation ID.

        Returns:
            Number of relationships.
        """
        result = await self.session.execute(
            select(func.count()).select_from(EntityRelationship).where(
                EntityRelationship.investigation_id == investigation_id,
                EntityRelationship.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one()

    async def create_version(
        self,
        investigation_id: str,
        version_number: int,
        graph_state: str,
        change_description: str | None = None,
        changed_by_id: str | None = None,
    ) -> InvestigationVersion:
        """Create a new version snapshot for undo/redo.

        Args:
            investigation_id: The investigation ID.
            version_number: The version number.
            graph_state: Serialized graph state.
            change_description: Description of the change.
            changed_by_id: ID of the user who made the change.

        Returns:
            The created InvestigationVersion.
        """
        version = InvestigationVersion(
            investigation_id=investigation_id,
            version_number=version_number,
            graph_state=graph_state,
            change_description=change_description,
            changed_by_id=changed_by_id,
        )
        self.session.add(version)
        await self.session.flush()
        await self.session.refresh(version)
        return version

    async def create_snapshot(
        self,
        investigation_id: str,
        name: str,
        graph_state: str,
        description: str | None = None,
        canvas_viewport: str | None = None,
        created_by_id: str | None = None,
    ) -> InvestigationSnapshot:
        """Create a named snapshot checkpoint.

        Args:
            investigation_id: The investigation ID.
            name: Snapshot name.
            graph_state: Serialized graph state.
            description: Optional description.
            canvas_viewport: Optional viewport state.
            created_by_id: ID of the creating user.

        Returns:
            The created InvestigationSnapshot.
        """
        snapshot = InvestigationSnapshot(
            investigation_id=investigation_id,
            name=name,
            graph_state=graph_state,
            description=description,
            canvas_viewport=canvas_viewport,
            created_by_id=created_by_id,
        )
        self.session.add(snapshot)
        await self.session.flush()
        await self.session.refresh(snapshot)
        return snapshot

    async def get_templates(self, workspace_id: str) -> list[Investigation]:
        """Get all investigation templates in a workspace.

        Args:
            workspace_id: The workspace ID.

        Returns:
            List of template investigations.
        """
        return await self.list(
            filters=[
                Investigation.workspace_id == workspace_id,
                Investigation.is_template == True,  # noqa: E712
            ]
        )
