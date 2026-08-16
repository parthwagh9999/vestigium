"""Task model for investigation case management.

Tasks track actionable work items within an investigation
(e.g., "Investigate registrant email", "Run WHOIS on related domains").
"""

from __future__ import annotations

import enum

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class TaskStatus(str, enum.Enum):
    """Task completion status."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    """Task priority level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Actionable work item within an investigation."""

    __tablename__ = "tasks"

    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=TaskStatus.TODO.value,
        nullable=False,
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        default=TaskPriority.MEDIUM.value,
        nullable=False,
    )
    assigned_to_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    entity_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("entities.id", ondelete="SET NULL"),
        nullable=True,
    )
    due_date: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        back_populates="tasks",
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title[:50]}, status={self.status})>"
