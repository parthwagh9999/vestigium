"""SavedSearch and SavedQuery models for persistent search operations."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SavedSearch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A saved search query that can be re-executed.

    Supports global search, entity search, relationship search,
    regex, boolean, and fuzzy query types.
    """

    __tablename__ = "saved_searches"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    query_type: Mapped[str] = mapped_column(String(50), nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    filters: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_global: Mapped[bool] = mapped_column(default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<SavedSearch(id={self.id}, name={self.name})>"


class SavedQuery(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A saved graph query for complex graph filtering and analysis."""

    __tablename__ = "saved_queries"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    query_language: Mapped[str] = mapped_column(String(50), default="json", nullable=False)
    created_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<SavedQuery(id={self.id}, name={self.name})>"
