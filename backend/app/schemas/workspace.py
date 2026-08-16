"""Workspace schemas."""

from __future__ import annotations

from pydantic import Field

from app.schemas.common import BaseSchema, TimestampSchema


class WorkspaceCreate(BaseSchema):
    """Create a new workspace."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    icon: str | None = None
    color: str | None = None


class WorkspaceUpdate(BaseSchema):
    """Update a workspace."""

    name: str | None = None
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    settings: str | None = None


class WorkspaceResponse(TimestampSchema):
    """Workspace response."""

    id: str
    name: str
    description: str | None = None
    owner_id: str | None = None
    icon: str | None = None
    color: str | None = None
    member_count: int = 0
    investigation_count: int = 0


class WorkspaceMemberAdd(BaseSchema):
    """Add a member to a workspace."""

    user_id: str
    role: str = "member"


class WorkspaceMemberResponse(BaseSchema):
    """Workspace member response."""

    user_id: str
    username: str
    full_name: str | None = None
    role: str
