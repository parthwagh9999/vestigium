"""Entity schemas for all 60+ entity types.

Provides create, update, and response schemas for entities
with type-specific property validation.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema, TimestampSchema


class EntityCreate(BaseSchema):
    """Create a new entity in an investigation."""

    investigation_id: str
    entity_type: str
    label: str = Field(min_length=1, max_length=500)
    value: str = Field(min_length=1, max_length=2000)
    properties: dict[str, Any] | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str | None = None
    icon: str | None = None
    color: str | None = None
    position_x: float = 0.0
    position_y: float = 0.0
    notes_text: str | None = None
    custom_fields: list[CustomFieldCreate] | None = None


class EntityBulkCreate(BaseSchema):
    """Bulk create entities."""

    investigation_id: str
    entities: list[EntityCreate]


class EntityUpdate(BaseSchema):
    """Update an entity."""

    label: str | None = None
    value: str | None = None
    entity_type: str | None = None
    properties: dict[str, Any] | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    source: str | None = None
    icon: str | None = None
    color: str | None = None
    position_x: float | None = None
    position_y: float | None = None
    is_pinned: bool | None = None
    notes_text: str | None = None
    group_id: str | None = None


class EntityPositionUpdate(BaseSchema):
    """Batch position update for drag/drop operations."""

    id: str
    position_x: float
    position_y: float


class EntityBulkPositionUpdate(BaseSchema):
    """Bulk position update request."""

    positions: list[EntityPositionUpdate]


from pydantic import Field, field_validator
import json


class EntityResponse(TimestampSchema):
    """Entity response schema."""

    id: str
    investigation_id: str
    entity_type: str
    label: str
    value: str
    properties: dict[str, Any] | None = None
    confidence: float
    source: str | None = None
    icon: str | None = None
    color: str | None = None
    position_x: float
    position_y: float
    is_pinned: bool = False
    notes_text: str | None = None
    group_id: str | None = None
    custom_fields: list[CustomFieldResponse] = Field(default_factory=list)

    @field_validator("properties", mode="before")
    @classmethod
    def parse_properties_json(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v


class EntityBriefResponse(BaseSchema):
    """Compact entity reference."""

    id: str
    entity_type: str
    label: str
    value: str
    icon: str | None = None
    color: str | None = None


class CustomFieldCreate(BaseSchema):
    """Create a custom field on an entity."""

    field_name: str = Field(min_length=1, max_length=255)
    field_value: str | None = None
    field_type: str = "text"


class CustomFieldResponse(BaseSchema):
    """Custom field response."""

    id: str
    field_name: str
    field_value: str | None = None
    field_type: str


class EntityHistoryResponse(TimestampSchema):
    """Entity change history entry."""

    id: str
    entity_id: str
    action: str
    changed_by_id: str | None = None
    changes: dict[str, Any] | None = None


class EntitySearchRequest(BaseSchema):
    """Search entities with filters."""

    query: str | None = None
    entity_types: list[str] | None = None
    investigation_id: str | None = None
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    max_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    sources: list[str] | None = None
    tags: list[str] | None = None
    use_regex: bool = False
    use_fuzzy: bool = False
