"""Relationship API endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_async_session
from app.dependencies import get_current_active_user
from app.models.user import User
from app.repositories.relationship import RelationshipRepository
from app.schemas.common import IDResponse, PaginatedResponse, SuccessResponse
from app.schemas.relationship import RelationshipCreate, RelationshipResponse, RelationshipUpdate

router = APIRouter()


@router.get("", response_model=PaginatedResponse[RelationshipResponse])
async def list_relationships(
    investigation_id: str = Query(...),
    relationship_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=500, ge=1, le=5000),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedResponse[RelationshipResponse]:
    """List relationships for an investigation."""
    repo = RelationshipRepository(session)
    offset = (page - 1) * page_size
    relationships = await repo.get_by_investigation(
        investigation_id, relationship_type=relationship_type, offset=offset, limit=page_size
    )
    total = await repo.count(filters=[repo.model.investigation_id == investigation_id])

    items = []
    for rel in relationships:
        resp = RelationshipResponse.model_validate(rel)
        if rel.properties:
            try:
                resp.properties = json.loads(rel.properties)
            except (json.JSONDecodeError, TypeError):
                resp.properties = None
        items.append(resp)

    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=IDResponse, status_code=201)
async def create_relationship(
    data: RelationshipCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> IDResponse:
    """Create a relationship between two entities."""
    repo = RelationshipRepository(session)
    properties_json = json.dumps(data.properties) if data.properties else None

    rel = await repo.upsert_relationship(
        investigation_id=data.investigation_id,
        source_entity_id=data.source_entity_id,
        target_entity_id=data.target_entity_id,
        relationship_type=data.relationship_type,
        label=data.label,
        weight=data.weight,
        confidence=data.confidence,
        source=data.source,
        properties=properties_json,
        is_bidirectional=data.is_bidirectional,
        color=data.color,
        style=data.style,
    )
    await session.commit()
    return IDResponse(id=rel.id, message="Relationship created")


@router.put("/{relationship_id}", response_model=RelationshipResponse)
async def update_relationship(
    relationship_id: str,
    data: RelationshipUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> RelationshipResponse:
    """Update a relationship."""
    repo = RelationshipRepository(session)
    update_data = data.model_dump(exclude_unset=True)

    if "properties" in update_data and update_data["properties"] is not None:
        update_data["properties"] = json.dumps(update_data["properties"])

    rel = await repo.update(relationship_id, **update_data)
    if not rel:
        raise NotFoundError("Relationship", relationship_id)
    await session.commit()
    return RelationshipResponse.model_validate(rel)


@router.delete("/{relationship_id}", response_model=SuccessResponse)
async def delete_relationship(
    relationship_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> SuccessResponse:
    """Delete a relationship."""
    repo = RelationshipRepository(session)
    if not await repo.delete(relationship_id):
        raise NotFoundError("Relationship", relationship_id)
    await session.commit()
    return SuccessResponse(message="Relationship deleted")
