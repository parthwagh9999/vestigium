"""Investigation schemas for CRUD operations and versioning."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, BaseModel

from app.schemas.common import BaseSchema, TimestampSchema


class InvestigationCreate(BaseSchema):
    """Create a new investigation."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    workspace_id: str
    priority: str = "medium"
    icon: str | None = None
    color: str | None = None
    template_id: str | None = None


class InvestigationUpdate(BaseSchema):
    """Update an investigation."""

    name: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    icon: str | None = None
    color: str | None = None
    graph_state: str | None = None
    canvas_viewport: str | None = None
    layout_config: str | None = None


class InvestigationResponse(TimestampSchema):
    """Investigation response with metadata."""

    id: str
    name: str
    description: str | None = None
    workspace_id: str
    owner_id: str | None = None
    status: str
    priority: str
    icon: str | None = None
    color: str | None = None
    is_template: bool = False
    current_version: int = 1
    entity_count: int = 0
    relationship_count: int = 0
    root_entity_id: str | None = None


class InvestigationDetailResponse(InvestigationResponse):
    """Detailed investigation response including graph state."""

    graph_state: str | None = None
    canvas_viewport: str | None = None
    layout_config: str | None = None


class BulkDeleteNodes(BaseModel):
    node_ids: list[str]


class InvestigationVersionResponse(TimestampSchema):
    """Version history entry response."""

    id: str
    investigation_id: str
    version_number: int
    change_description: str | None = None
    changed_by_id: str | None = None


class InvestigationSnapshotCreate(BaseSchema):
    """Create a named snapshot."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class InvestigationSnapshotResponse(TimestampSchema):
    """Snapshot response."""

    id: str
    investigation_id: str
    name: str
    description: str | None = None
    created_by_id: str | None = None
