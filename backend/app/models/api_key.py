"""API Key Vault model for secure storage of third-party API keys.

All values are encrypted at rest using Fernet symmetric encryption.
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class APIKeyVault(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Encrypted storage for third-party API keys and secrets.

    Secrets are encrypted using Fernet symmetric encryption
    before being stored in the database. The encryption key
    is configured via the ENCRYPTION_KEY environment variable.
    """

    __tablename__ = "api_key_vault"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    key_name: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_used_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    usage_count: Mapped[int] = mapped_column(default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<APIKeyVault(service={self.service_name}, key={self.key_name})>"
