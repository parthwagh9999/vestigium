"""Evidence, Attachment, and SourceURL models for case management.

Evidence tracks the provenance of intelligence data with chain of custody,
confidence scoring, raw responses, and analyst notes.
"""

from __future__ import annotations

import enum

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class EvidenceType(str, enum.Enum):
    """Classification of evidence items."""
    RAW_RESPONSE = "raw_response"
    SCREENSHOT = "screenshot"
    DOCUMENT = "document"
    API_RESPONSE = "api_response"
    MANUAL_ENTRY = "manual_entry"
    TRANSFORM_OUTPUT = "transform_output"
    IMPORT = "import"


class Evidence(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Evidence item linking intelligence data to its source.

    Maintains chain of custody with timestamps, analyst notes,
    confidence scoring, and raw response storage.
    """

    __tablename__ = "evidence"

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
    relationship_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("entity_relationships.id", ondelete="SET NULL"),
        nullable=True,
    )
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    analyst_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    collected_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    transform_run_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("transform_runs.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        back_populates="evidence_items",
    )
    source_urls: Mapped[list[SourceURL]] = relationship(
        "SourceURL",
        back_populates="evidence",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    attachments: Mapped[list[Attachment]] = relationship(
        "Attachment",
        back_populates="evidence",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Evidence(id={self.id}, title={self.title[:50]})>"


class SourceURL(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """URL source reference for an evidence item."""

    __tablename__ = "source_urls"

    evidence_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    accessed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    evidence: Mapped[Evidence] = relationship(
        "Evidence",
        back_populates="source_urls",
    )

    def __repr__(self) -> str:
        return f"<SourceURL(id={self.id}, url={self.url[:80]})>"


class Attachment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """File attachment linked to an evidence item."""

    __tablename__ = "attachments"

    evidence_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    evidence: Mapped[Evidence] = relationship(
        "Evidence",
        back_populates="attachments",
    )

    def __repr__(self) -> str:
        return f"<Attachment(id={self.id}, filename={self.filename})>"
