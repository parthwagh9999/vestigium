"""Workspace model for organizing investigations and team collaboration.

Workspaces provide multi-tenant isolation and team-based access control.
Each workspace can contain multiple investigations and have multiple members.
"""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DescriptionMixin, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

workspace_members = Table(
    "workspace_members",
    Base.metadata,
    Column("workspace_id", String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role", String(50), default="member"),
)


class Workspace(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, DescriptionMixin):
    """A workspace groups investigations and provides team-based access control.

    Workspaces support:
        - Multiple investigations
        - Team membership with workspace-level roles
        - Shared settings and API key configurations
        - Investigation templates
    """

    __tablename__ = "workspaces"

    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    settings: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    members: Mapped[list] = relationship(
        "User",
        secondary=workspace_members,
        back_populates="workspaces",
        lazy="selectin",
    )
    investigations: Mapped[list] = relationship(
        "Investigation",
        back_populates="workspace",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Workspace(id={self.id}, name={self.name})>"
