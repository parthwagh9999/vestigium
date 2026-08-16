"""Tag model for categorizing entities, investigations, and evidence.

Tags are investigation-scoped and support color coding for visual organization.
"""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# ---- Association Tables ----

entity_tags = Table(
    "entity_tags",
    Base.metadata,
    Column("entity_id", String(36), ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

investigation_tags = Table(
    "investigation_tags",
    Base.metadata,
    Column("investigation_id", String(36), ForeignKey("investigations.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A color-coded tag for categorizing entities and investigations.

    Tags are scoped to a workspace and can be applied to both
    entities and investigations for cross-cutting organization.
    """

    __tablename__ = "tags"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    color: Mapped[str] = mapped_column(String(20), default="#6B7280", nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name})>"
