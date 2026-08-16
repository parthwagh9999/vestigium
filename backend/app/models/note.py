"""Note model for analyst annotations on investigations and entities."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Note(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Free-form analyst note attached to an investigation or entity.

    Notes support Markdown formatting and can be pinned for visibility.
    """

    __tablename__ = "notes"

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
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(default=False, nullable=False)
    author_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        back_populates="notes",
    )

    def __repr__(self) -> str:
        title_preview = self.title or self.content[:30]
        return f"<Note(id={self.id}, title={title_preview})>"
