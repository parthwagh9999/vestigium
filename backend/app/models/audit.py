"""Audit log model for tracking all user actions.

Every significant operation (create, update, delete, transform execution, etc.)
is logged with the acting user, timestamp, and before/after state.
"""

from __future__ import annotations

import enum

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AuditAction(str, enum.Enum):
    """Types of auditable actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"
    TRANSFORM_RUN = "transform_run"
    PLUGIN_INSTALL = "plugin_install"
    PLUGIN_UNINSTALL = "plugin_uninstall"
    PERMISSION_CHANGE = "permission_change"
    SETTINGS_CHANGE = "settings_change"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Immutable audit log entry tracking user actions.

    Attributes:
        user_id: The user who performed the action.
        action: The type of action performed.
        resource_type: The type of resource affected (e.g., "investigation", "entity").
        resource_id: The ID of the affected resource.
        details: JSON-serialized details of the action.
        ip_address: The IP address of the client.
        user_agent: The user agent string of the client.
        before_state: JSON-serialized state before the action.
        after_state: JSON-serialized state after the action.
    """

    __tablename__ = "audit_logs"

    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    before_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    investigation_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="audit_logs",
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, resource={self.resource_type})>"
