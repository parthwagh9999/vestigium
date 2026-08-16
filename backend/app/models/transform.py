"""Transform execution models.

Tracks transform runs (execution of OSINT data gathering operations)
and their results, including input/output entities, duration, and errors.
"""

from __future__ import annotations

import enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TransformStatus(str, enum.Enum):
    """Status of a transform execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TransformRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Record of a single transform execution.

    Tracks the full lifecycle of a transform from submission to completion,
    including timing, input/output entity counts, and error details.
    """

    __tablename__ = "transform_runs"

    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transform_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    transform_name: Mapped[str] = mapped_column(String(255), nullable=False)
    plugin_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=TransformStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    input_entity_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("entities.id", ondelete="SET NULL"),
        nullable=True,
    )
    input_entity_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_params: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    entities_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    relationships_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[str | None] = mapped_column(Text, nullable=True)
    triggered_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    parent_run_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("transform_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_recursive: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_bulk: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_scheduled: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    results: Mapped[list[TransformResult]] = relationship(
        "TransformResult",
        back_populates="transform_run",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<TransformRun(id={self.id}, transform={self.transform_name}, status={self.status})>"


class TransformResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Individual result item from a transform execution.

    Each result represents either a new entity or relationship
    created by the transform, with raw response data preserved.
    """

    __tablename__ = "transform_results"

    transform_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("transform_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    result_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("entities.id", ondelete="SET NULL"),
        nullable=True,
    )
    relationship_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("entity_relationships.id", ondelete="SET NULL"),
        nullable=True,
    )
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Relationships
    transform_run: Mapped[TransformRun] = relationship(
        "TransformRun",
        back_populates="results",
    )

    def __repr__(self) -> str:
        return f"<TransformResult(id={self.id}, type={self.result_type})>"
