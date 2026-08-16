"""Timeline event model for investigation timeline visualization."""

from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TimelineEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An event on the investigation timeline.

    Timeline events can be auto-generated from entity/relationship creation
    or manually added by analysts. They support ordering by event_time
    for chronological investigation reconstruction.
    """

    __tablename__ = "timeline_events"

    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("entities.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_time: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_auto_generated: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        back_populates="timeline_events",
    )

    def __repr__(self) -> str:
        return f"<TimelineEvent(id={self.id}, title={self.title[:50]})>"
