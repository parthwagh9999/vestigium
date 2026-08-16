"""Investigation model with versioning, snapshots, and graph state.

An investigation is the core working unit — it contains entities,
relationships, evidence, and the full graph state for link analysis.
"""

from __future__ import annotations

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DescriptionMixin, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

import enum


class InvestigationStatus(str, enum.Enum):
    """Status of an investigation."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class InvestigationPriority(str, enum.Enum):
    """Priority level for an investigation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Investigation(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, DescriptionMixin):
    """An investigation containing entities, relationships, and evidence.

    Supports:
        - Full graph state serialization
        - Version history with snapshots
        - Status tracking and prioritization
        - Tags, bookmarks, and notes
        - Template creation from existing investigations
    """

    __tablename__ = "investigations"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=InvestigationStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        default=InvestigationPriority.MEDIUM.value,
        nullable=False,
    )
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    template_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="SET NULL"),
        nullable=True,
    )
    root_entity_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("entities.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )
    graph_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    canvas_viewport: Mapped[str | None] = mapped_column(Text, nullable=True)
    layout_config: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    workspace: Mapped["Workspace"] = relationship(
        "Workspace",
        back_populates="investigations",
        lazy="selectin",
    )
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="investigations",
        lazy="selectin",
    )
    entities: Mapped[list] = relationship(
        "Entity",
        back_populates="investigation",
        lazy="noload",
        cascade="all, delete-orphan",
        foreign_keys="[Entity.investigation_id]"
    )
    relationships: Mapped[list] = relationship(
        "EntityRelationship",
        back_populates="investigation",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    versions: Mapped[list[InvestigationVersion]] = relationship(
        "InvestigationVersion",
        back_populates="investigation",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    snapshots: Mapped[list[InvestigationSnapshot]] = relationship(
        "InvestigationSnapshot",
        back_populates="investigation",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    evidence_items: Mapped[list] = relationship(
        "Evidence",
        back_populates="investigation",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    notes: Mapped[list] = relationship(
        "Note",
        back_populates="investigation",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    bookmarks: Mapped[list] = relationship(
        "Bookmark",
        back_populates="investigation",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list] = relationship(
        "Task",
        back_populates="investigation",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    timeline_events: Mapped[list] = relationship(
        "TimelineEvent",
        back_populates="investigation",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Investigation(id={self.id}, name={self.name}, status={self.status})>"


class InvestigationVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Version record for investigation state — enables undo/redo.

    Each version stores a complete serialized snapshot of the graph state
    at a point in time, along with a description of what changed.
    """

    __tablename__ = "investigation_versions"

    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    graph_state: Mapped[str] = mapped_column(Text, nullable=False)
    change_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    investigation: Mapped[Investigation] = relationship(
        "Investigation",
        back_populates="versions",
    )

    def __repr__(self) -> str:
        return f"<InvestigationVersion(investigation_id={self.investigation_id}, v={self.version_number})>"


class InvestigationSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Named snapshot of an investigation for manual save points.

    Unlike versions (automatic), snapshots are user-created named checkpoints
    that can be restored at any time.
    """

    __tablename__ = "investigation_snapshots"

    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    graph_state: Mapped[str] = mapped_column(Text, nullable=False)
    canvas_viewport: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    investigation: Mapped[Investigation] = relationship(
        "Investigation",
        back_populates="snapshots",
    )

    def __repr__(self) -> str:
        return f"<InvestigationSnapshot(id={self.id}, name={self.name})>"
