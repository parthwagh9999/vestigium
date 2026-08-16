"""User, Role, and Permission models for authentication and RBAC.

Implements a full role-based access control system with many-to-many
relationships between Users ↔ Roles and Roles ↔ Permissions.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

# ---- Association Tables ----

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Application user with authentication credentials and RBAC roles."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    preferences: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    roles: Mapped[list[Role]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )
    workspaces: Mapped[list] = relationship(
        "Workspace",
        secondary="workspace_members",
        back_populates="members",
        lazy="selectin",
    )
    investigations: Mapped[list] = relationship(
        "Investigation",
        back_populates="owner",
        lazy="noload",
    )
    audit_logs: Mapped[list] = relationship(
        "AuditLog",
        back_populates="user",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Named role that groups permissions together for RBAC."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    users: Mapped[list[User]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
        lazy="noload",
    )
    permissions: Mapped[list[Permission]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"


class Permission(Base, UUIDPrimaryKeyMixin):
    """Individual permission that can be assigned to roles.

    Permissions follow a resource:action naming convention, e.g.:
        - investigation:create
        - investigation:read
        - investigation:update
        - investigation:delete
        - entity:create
        - transform:execute
        - admin:manage_users
        - plugin:install
    """

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    roles: Mapped[list[Role]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Permission(name={self.name})>"
