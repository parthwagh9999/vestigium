"""Plugin and PluginConfig models for the extensible plugin system.

Tracks installed plugins, their configuration, health status, and API key
requirements.
"""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PluginStatus(str, enum.Enum):
    """Plugin installation status."""
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UPDATING = "updating"


class InstalledPlugin(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Record of an installed plugin with its manifest metadata.

    Attributes:
        plugin_id: Unique identifier from the plugin manifest.
        name: Human-readable plugin name.
        version: Installed version string.
        description: Plugin description.
        author: Plugin author.
        icon: Icon identifier or URL.
        status: Current plugin status.
        manifest: Full JSON-serialized plugin manifest.
        permissions: JSON array of required permissions.
        dependencies: JSON array of plugin dependencies.
        config_schema: JSON schema for plugin configuration.
        health_check_url: URL for plugin health check endpoint.
        update_channel: Update channel URL for auto-updates.
    """

    __tablename__ = "installed_plugins"

    plugin_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=PluginStatus.ENABLED.value,
        nullable=False,
    )
    manifest: Mapped[str | None] = mapped_column(Text, nullable=True)
    permissions: Mapped[str | None] = mapped_column(Text, nullable=True)
    dependencies: Mapped[str | None] = mapped_column(Text, nullable=True)
    config_schema: Mapped[str | None] = mapped_column(Text, nullable=True)
    health_check_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    update_channel: Mapped[str | None] = mapped_column(String(500), nullable=True)
    installed_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_health_check: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    configs: Mapped[list[PluginConfig]] = relationship(
        "PluginConfig",
        back_populates="plugin",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<InstalledPlugin(plugin_id={self.plugin_id}, version={self.version})>"


class PluginConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Configuration key-value pair for a plugin.

    Sensitive values (API keys, secrets) are encrypted at rest using
    the application's encryption service.
    """

    __tablename__ = "plugin_configs"

    plugin_db_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("installed_plugins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    plugin: Mapped[InstalledPlugin] = relationship(
        "InstalledPlugin",
        back_populates="configs",
    )

    def __repr__(self) -> str:
        return f"<PluginConfig(plugin={self.plugin_db_id}, key={self.key})>"
