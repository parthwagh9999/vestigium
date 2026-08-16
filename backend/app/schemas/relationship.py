"""Relationship schemas."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema, TimestampSchema


class RelationshipCreate(BaseSchema):
    """Create a relationship between two entities."""

    investigation_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    label: str | None = None
    weight: float = 1.0
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str | None = None
    properties: dict[str, Any] | None = None
    is_bidirectional: bool = False
    color: str | None = None
    style: str | None = None


class RelationshipBulkCreate(BaseSchema):
    """Bulk create relationships."""

    investigation_id: str
    relationships: list[RelationshipCreate]


class RelationshipUpdate(BaseSchema):
    """Update a relationship."""

    relationship_type: str | None = None
    label: str | None = None
    weight: float | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    source: str | None = None
    properties: dict[str, Any] | None = None
    is_bidirectional: bool | None = None
    color: str | None = None
    style: str | None = None


class RelationshipResponse(TimestampSchema):
    """Relationship response schema."""

    id: str
    investigation_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    label: str | None = None
    weight: float
    confidence: float
    source: str | None = None
    properties: dict[str, Any] | None = None
    is_bidirectional: bool = False
    color: str | None = None
    style: str | None = None
